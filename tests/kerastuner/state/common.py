import json


def is_serializable(state):
    conf = state.to_config()
    # serialize and deserialize
    json_conf = json.loads(json.dumps(conf))
    assert conf == json_conf
