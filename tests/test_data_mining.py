import argparse
import logging
import os
import random
import yaml
import numpy as np
from vocaludf.model_udf import *

logging.basicConfig()
logger = logging.getLogger("vocaludf")
logger.setLevel(logging.DEBUG)

class TestDataMining(GQARelationshipBalancedModelDistiller):
    pass

if __name__ == "__main__":
    config = yaml.safe_load(
        open("/gscratch/balazinska/enhaoz/VOCAL-UDF/configs/config.yaml", "r")
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--run_id", type=int, help="run id")
    parser.add_argument("--dataset", type=str, help="dataset name")
    parser.add_argument("--relationship", type=str, help="Relationship name")
    parser.add_argument("--n_train", type=int, help="number of training samples")
    parser.add_argument("--save_labeled_data", action="store_true", help="save labeled data")
    parser.add_argument("--load_labeled_data", action="store_true", help="load labeled data")

    args = parser.parse_args()
    run_id = args.run_id
    dataset = args.dataset
    relationship = args.relationship
    n_train = args.n_train
    save_labeled_data = args.save_labeled_data
    load_labeled_data = args.load_labeled_data

    random.seed(run_id)
    np.random.seed(run_id)

    """
    Set up logging
    """
    # Create a directory if it doesn't already exist
    log_dir = os.path.join(config["log_dir"], "test_data_mining", dataset, f"{model_distiller.llm_method}_{model_distiller.mlp_method}")
    os.makedirs(
        log_dir,
        exist_ok=True,
    )

    # Create a file handler that logs even debug messages
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"udf-{relationship}_run-{run_id}_ntrain-{n_train}.log"),
        mode="w",
    )
    file_handler.setLevel(logging.DEBUG)

    # Create a console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatters and add them to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    prompt_config = yaml.load(
        open(os.path.join(config["prompt_dir"], "prompt.yaml"), "r"),
        Loader=yaml.FullLoader,
    )

    name_map = {
        "on": {"signature": "On(o0, o1)", "description": "Whether o0 is on o1."},
        "wearing": {"signature": "Wearing(o0, o1)", "description": "Whether o0 is wearing o1."},
        "near": {"signature": "Near(o0, o1)", "description": "Whether o0 is near o1."},
        "holding": {"signature": "Holding(o0, o1)", "description": "Whether o0 is holding o1."},
        "to_the_right_of": {"signature": "to_the_right_of(o0, o1)", "description": "Whether o0 is to the right of o1."},
        "riding": {"signature": "Riding(o0, o1)", "description": "Whether o0 is riding o1."},
    }
    udf_signature = name_map[relationship]["signature"]
    udf_description = name_map[relationship]["description"]

    md = TestDataMining(config, prompt_config, dataset, udf_signature, udf_description, run_id, n_train=1000, save_labeled_data, load_labeled_data)