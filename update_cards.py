from card import CardLearner
from main import file_prefix

if __name__ == '__main__':
    card_learner = CardLearner(file_prefix)
    card_learner.update()
