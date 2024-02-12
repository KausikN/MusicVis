"""
Note Generator Library - Random Sequence

Generation Logic:
- Notes have a set number of possible values, say N = {n1, n2, ... nk}
    - N is set of all possible notes
    - k is number of possible notes
- We need to generate a sequence of notes each with a value and parameters
    - Value is simply a random selection from possible notes
        - This is done using a probability distribution which can be kept constant or made to change based on previous notes
    - Parameters
        - Float parameters can be generated randomly within a set range or kept constant
"""

# Imports
import numpy as np
from tqdm import tqdm

# Main Vars


# Main Functions
## Note Generation Environment Functions
def NoteGenEnv_Update_ConstantRandomDistribution(NOTES_DATA, VALUE_GEN_MAP={}):
    '''
    Note Generator Environment - Update - Constant Random Distribution

    Parameters,
    - NOTES_DATA : All data about the generated notes
        - "notes": List of generated notes
        - "env_data": Environment data used by the function
        - "map_value_name": Map to get the name of a note for each possible value
    - VALUE_GEN_MAP : Map to get the generation data for value and parameters for each possible note value
        - "prob": Probability of selection of the note (Constant)
        - "params": For each parameter, info related to generation
            - "type": Type of parameter generation, can be,
                - "constant": Directly takes the "value" key data and assigns to the parameter
                - "number": Takes the range from "range" key data and generates a random value within the range to assign to the parameter
                - "selection": Selects a random option from "options" key data list and assigns to the parameter (can give probability distribution in "prob" key data as a list)
    '''
    # Init
    np.random.seed(NOTES_DATA["env_data"]["seed"])
    POSSIBLE_NOTE_VALUES = list(VALUE_GEN_MAP.keys())
    # Generate next note
    NOTE_NEXT = {}
    ## Select value
    PROB_DIST = np.array([VALUE_GEN_MAP[v]["prob"] for v in POSSIBLE_NOTE_VALUES])
    PROB_DIST = PROB_DIST / np.sum(PROB_DIST)
    NOTE_NEXT["value"] = np.random.choice(POSSIBLE_NOTE_VALUES, p=PROB_DIST)
    NOTE_NEXT["note"] = NOTES_DATA["map_value_name"][NOTE_NEXT["value"]]
    ## Generate parameters
    PARAMS_GEN_DATA = VALUE_GEN_MAP[NOTE_NEXT["value"]]["params"]
    for pk in PARAMS_GEN_DATA.keys():
        ### Constant
        if PARAMS_GEN_DATA[pk]["type"] == "constant":
            NOTE_NEXT[pk] = PARAMS_GEN_DATA[pk]["value"]
        ### Number
        elif PARAMS_GEN_DATA[pk]["type"] == "number":
            NOTE_NEXT[pk] = round(
                PARAMS_GEN_DATA[pk]["range"][0] + np.random.rand() * (PARAMS_GEN_DATA[pk]["range"][1] - PARAMS_GEN_DATA[pk]["range"][0]), 
                ndigits=2
            )
        ### Selection
        elif PARAMS_GEN_DATA[pk]["type"] == "selection":
            param_options = PARAMS_GEN_DATA[pk]["options"]
            if "prob" not in PARAMS_GEN_DATA[pk].keys(): PARAMS_GEN_DATA[pk]["prob"] = [1.0/len(param_options)] * len(param_options)
            OPTIONS_PROB_DIST = np.array(PARAMS_GEN_DATA[pk]["prob"])
            OPTIONS_PROB_DIST = OPTIONS_PROB_DIST / np.sum(OPTIONS_PROB_DIST)
            NOTE_NEXT[pk] = np.random.choice(param_options, p=OPTIONS_PROB_DIST)
        ### Else
        else:
            pass

    NOTES_DATA["notes"].append(NOTE_NEXT)
    return NOTES_DATA


## Note Generator Functions
def RandomSequence_GenerateNotes(N, ENV_UPDATE_FUNC, MAPS, seed=0, PREV_NOTES=[]):
    '''
    Random Sequence - Generate Notes

    Parameters,
    - "N": Number of notes to generate
    - "env_update_func": Function to use for note generation
    - "maps": Mapping dictionaries
        - "value_name": Maps note value to its name
        - "name_value": Maps note name to its value
    '''
    # Init
    np.random.seed(seed)
    NOTES_DATA = {
        "notes": PREV_NOTES,
        "env_data": {
            "seed": seed
        },
        "map_value_name": MAPS["value_name"]
    }
    # Iterate
    for i in tqdm(range(N), disable=True):
        ## Set new seed
        NOTES_DATA["env_data"]["seed"] = np.random.randint(0, 101)
        ## Generate Note
        NOTES_DATA = ENV_UPDATE_FUNC(NOTES_DATA)

    return NOTES_DATA

# Main Vars
NOTEGENENV_UPDATE_FUNCS = {
    "Constant Random Distribution": NoteGenEnv_Update_ConstantRandomDistribution
}

# RunCode      
