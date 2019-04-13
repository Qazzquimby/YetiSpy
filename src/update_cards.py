from src.card import CardLearner
from src.main import file_prefix

if __name__ == '__main__':
    card_learner = CardLearner(file_prefix)
    card_learner.update()
