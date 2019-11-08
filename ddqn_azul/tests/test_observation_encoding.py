from ddqn_azul.azul_simulator import AzulSimulator
import pickle
import os

MOVES = [(0, 1, 2, 1)]

HERE = os.path.dirname(__file__)


def test_encoding():
    with open(os.path.join(HERE, 'azs.pkl'), 'rb') as pkl:
        azs = pickle.load(pkl)
    for move in MOVES:
        azs.act(*move)
        dup = AzulSimulator(2)
        dup.initialize_from_obs(azs.get_obs())
        assert dup == azs
