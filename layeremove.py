#!/usr/bin/env python

import hashlib
import json
import os
from os.path import join
import sys


def write_blob(blob):
  sha256 = hashlib.sha256(blob.encode("ascii")).hexdigest()
  blob_path = join(oci_dir, "blobs", "sha256", sha256)
  if os.path.isfile(blob_path):
    print("{} already exists, skipping.".format(sha256))
    return sha256
  with open(blob_path, "w") as f:
    f.write(blob)
  print("{} added to blob store".format(sha256))
  return sha256


oci_dir = sys.argv[1]


index_data = json.load(open(join(oci_dir, "index.json")))
must_write_index = False
for manifest in index_data["manifests"]:
  digest_hash = manifest["digest"]
  digest_path = join(oci_dir, "blobs", digest_hash.replace(":", "/"))
  print("Found image manifest: "+digest_path)
  digest_data = json.load(open(digest_path))
  config_hash = digest_data["config"]["digest"]
  config_path = join(oci_dir, "blobs", config_hash.replace(":", "/"))
  config_data = json.load(open(config_path))
  print("Architecture={architecture}, OS={os}".format(**config_data))

  layer_position_in_history = []
  history_pos = 0
  for layer_pos in range(len(digest_data["layers"])):
    while config_data["history"][history_pos].get("empty_layer"):
      history_pos += 1
    layer_position_in_history.append(history_pos)
    history_pos += 1

  hashes_to_remove = sys.argv[2:][::]
  history = [layer for layer in config_data["history"] if not layer.get("empty_layer")]
  for layer, history, position in zip(digest_data["layers"], history, layer_position_in_history):
    if "#LAYEREMOVE#" in history["created_by"]:
      hashes_to_remove.append(layer["digest"])
    print("- layer {digest}, size {size} bytes ({created_by}), #{position} in history".format(
      digest=layer["digest"], size=layer["size"],
      created_by=history["created_by"], position=position))

  must_write_config = False
  for layer_pos in reversed(range(len(digest_data["layers"]))):
    if digest_data["layers"][layer_pos]["digest"] in hashes_to_remove:
      print("Removing layer #{}.".format(layer_pos))
      digest_data["layers"].pop(layer_pos)
      config_data["rootfs"]["diff_ids"].pop(layer_pos)
      config_data["history"][layer_position_in_history[layer_pos]]["created_by"] += "[REMOVED]"
      config_data["history"][layer_position_in_history[layer_pos]]["empty_layer"] = True
      must_write_config = True

  if must_write_config:
    new_config_hash = write_blob(json.dumps(config_data))
    digest_data["config"]["digest"] = "sha256:" + new_config_hash
    digest_data["config"]["size"] = os.stat(join(oci_dir, "blobs", "sha256", new_config_hash)).st_size
    new_digest_hash = write_blob(json.dumps(digest_data))
    manifest["digest"] = "sha256:" + new_digest_hash
    manifest["size"] = os.stat(join(oci_dir, "blobs", "sha256", new_digest_hash)).st_size
    must_write_index = True

if must_write_index:
  with open(join(oci_dir, "index.json"), "w") as f:
    json.dump(index_data, f)



