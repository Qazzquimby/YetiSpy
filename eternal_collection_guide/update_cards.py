from eternal_collection_guide.card import CardLearner
from eternal_collection_guide.generate_overall_value import file_prefix

if __name__ == '__main__':
    card_learner = CardLearner(file_prefix)
    card_learner.update()