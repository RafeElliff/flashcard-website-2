from flask import Flask, request, render_template, redirect, url_for, session
from forms import NewSetForm, NewCardForm, ChooseSetForm, StudySetForm
import os
from dotenv import load_dotenv
import json
import random
import logging

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv("flask_secret_key")

logging.basicConfig(level=logging.DEBUG)


class FlashcardSet:
    def __init__(self, name, flashcards_list):
        self.name = name
        if flashcards_list:
            self.flashcards_list = flashcards_list
        else:
            self.flashcards_list = []

    def add_new_card(self, card):
        card = card.into_json()
        self.flashcards_list.append(card)

    def into_json(self):
        as_dict = self.__dict__
        as_json = json.dumps(as_dict)
        return as_json

    def get_card_to_study(self):
        valid_cards = []
        weightings = []
        not_seen_before_cards = []
        for card in self.flashcards_list:
            valid_cards.append(card)
            card = Flashcard.out_of_json(card)
            # if card.times_seen == 0:
            #     not_seen_before_cards.append(card.into_json())
            weightings.append(11 - (card.learn_score))
        # if not_seen_before_cards:
        #     return Flashcard.out_of_json(random.choice(not_seen_before_cards))
        # else:
        choices = random.choices(valid_cards, weightings, k=1)
        return Flashcard.out_of_json(choices[0])

    def __repr__(self):
        return self.into_json()

    def update_card(self, new_card):
        flashcards_list = self.flashcards_list
        new_card_term, new_card_definition = new_card.term, new_card.definition
        new_card_json = new_card.into_json()
        for card in flashcards_list:
            card_as_dict = json.loads(card)
            if card_as_dict["term"] == new_card_term and card_as_dict["definition"] == new_card_definition:
                index = flashcards_list.index(card)
                flashcards_list[index] = new_card_json
        return self

    @classmethod
    def out_of_json(cls, json_string):
        data = json.loads(json_string)
        return cls(name=data["name"], flashcards_list=data["flashcards_list"])


class Flashcard:
    def __init__(self, term, definition, learn_score, times_seen):
        self.term = term
        self.definition = definition
        self.learn_score = learn_score
        self.times_seen = times_seen

    def __repr__(self):
        return self.into_json()

    def correct_answer(self):
        if self.times_seen == 0:
            self.learn_score = min(self.learn_score + 10, 10)
        else:
            self.learn_score = min(self.learn_score + 1, 10)
        self.times_seen = self.times_seen + 1

    def incorrect_answer(self):
        if self.learn_score == 10:
            self.learn_score = 5
        else:
            self.learn_score = max(self.learn_score - 1, 0)
            self.times_seen = self.times_seen + 1

    def into_json(self):
        as_dict = self.__dict__
        as_json = json.dumps(as_dict)
        return as_json

    @classmethod
    def out_of_json(cls, json_string):
        data = json.loads(json_string)
        return cls(term=data["term"], definition=data["definition"], learn_score=data["learn_score"],
                   times_seen=data["times_seen"])


def write_from_f_to_f(file1, file2):
    with open(file1, "r") as file:
        lines = file.readlines()
    with open(file2, "w") as file:
        for line in lines:
            file.write(line.strip("\n") + "\n")


def is_valid_json(string):
    try:
        json.loads(string)
        return True
    except:
        return False


def get_flashcard_set_from_json():
    chosen_set = session.get("Chosen Set")
    with open("flashcard set data/flashcard_sets.txt", "r") as file:
        flashcard_sets = file.readlines()
    for flashcard_set_as_json in flashcard_sets:
        flashcard_set = FlashcardSet.out_of_json(flashcard_set_as_json)
        if flashcard_set.name == chosen_set:
            return flashcard_set
    return "Set not found"


def read_lines(filename):
    with open(filename, "r") as file:
        return file.readlines()


def add_new_card_set(card_set):
    with open("flashcard set data/flashcard_sets.txt", "r") as file:
        lines = file.readlines()
    with open("flashcard set data/flashcard_sets.txt", "w") as file:
        lines.append(card_set)
        for line in lines:
            file.write(line.strip("\n") + "\n")


def get_list_of_card_sets():
    names = []
    with open("flashcard set data/flashcard_sets.txt", "r") as file:
        lines = file.readlines()
        for line in lines:
            flashcard_set = FlashcardSet.out_of_json(line)
            name = flashcard_set.name
            names.append(name)
    return names


def update_card_sets(new_flashcard_set):
    new_card_set_dict = new_flashcard_set.__dict__
    chosen_card_set = get_flashcard_set_from_json()
    chosen_set_name = chosen_card_set.name
    index = 0
    index_to_update = None
    lines = read_lines("flashcard set data/flashcard_sets.txt")
    for line in lines:
        set_on_line = json.loads(line)
        if set_on_line["name"].strip("") == chosen_set_name.strip(""):
            index_to_update = index
        index = (index + 1)
    if index_to_update is not None:
        lines[index_to_update] = new_card_set_dict
    with open("flashcard set data/flashcard_sets.txt", "w") as file:
        for line in lines:
            if is_valid_json(line) is True:
                line = line.strip("\n") + "\n"
                file.write(line)
            else:
                line = json.dumps(line)
                line = line.strip("\n") + "\n"
                file.write(line)


def initialise():
    session.clear()
    with open("terms and definitions/set_currently_being_created", "w"):
        pass


@app.route('/')
def index():
    initialise()
    return render_template("index.html")


@app.route('/initialise_new_set', methods=["GET", "POST"])
def initialise_new_set():
    form = NewSetForm(request.form)
    if request.method == "POST":
        name = request.form["Name"]
        with open("terms and definitions/set_currently_being_created", "w") as file:
            file.write(FlashcardSet(name, []).into_json())
        return redirect(url_for("add_new_flashcard"))
    return render_template("initialise_new_set.html", form=form)


@app.route("/add_new_flashcard", methods=["GET", "POST"])
def add_new_flashcard():
    new_card_form = NewCardForm(request.form)
    with open("terms and definitions/set_currently_being_created", "r") as file:
        set_json = file.read()
    flashcard_set = FlashcardSet.out_of_json(set_json)
    name = flashcard_set.name
    if request.method == "POST":
        term = request.form["Term"]
        definition = request.form["Definition"]
        flashcard = Flashcard(term, definition, 3, 0)
        flashcard_set.add_new_card(flashcard)
        with open("terms and definitions/set_currently_being_created", "w") as file:
            file.write(flashcard_set.into_json())

        return redirect(url_for("add_new_flashcard"))

    return render_template("add_new_flashcard.html", name=name, form=new_card_form)


@app.route("/create_cards_from_files")
def create_cards_from_files():
    with open("terms and definitions/set_currently_being_created", "r") as file:
        set_json = file.read()
    flashcard_set = FlashcardSet.out_of_json(set_json)
    with open("terms and definitions/terms.txt", "r") as file:
        terms = file.readlines()
    with open("terms and definitions/definitions.txt", "r") as file:
        definitions = file.readlines()
    for index in range(0, min(len(terms), len(definitions))):
        term = terms[index].strip("\n")
        definition = definitions[index].strip("\n")
        new_flashcard = Flashcard(term, definition, 3, 0)
        flashcard_set.add_new_card(new_flashcard)
    with open("terms and definitions/terms.txt", "w"):
        pass
    with open("terms and definitions/definitions.txt", "w"):
        pass
    with open("terms and definitions/set_currently_being_created", "w") as file:
        file.write(flashcard_set.into_json())
    return redirect(url_for("finish_set"))


@app.route('/finish_set')
def finish_set():
    if session.get("Finished Set"):
        finished_set = session.get("Flashcard Set")
    else:
        with open("terms and definitions/set_currently_being_created", "r") as file:
            finished_set = file.read()
    add_new_card_set(finished_set)
    return redirect(url_for("index"))


@app.route('/edit_set', methods=["GET", "POST"])
def edit_set():

    return render_template("edit_set.html")

@app.route("/reset_set_progress")
def reset_set_progress():
    chosen_set = get_flashcard_set_from_json()
    for index in range(0, len(chosen_set.flashcards_list)):
        flashcard = Flashcard.out_of_json(chosen_set.flashcards_list[index])
        flashcard.learn_score = 3
        flashcard.times_seen = 0
        chosen_set.flashcards_list[index] = flashcard.into_json()
    update_card_sets(chosen_set)
    return redirect(url_for("edit_set"))



@app.route('/choose_set', methods=["GET", "POST"])
def choose_set():
    choices = []
    form_action = ""
    flashcard_sets = get_list_of_card_sets()
    for flashcard_set in flashcard_sets:
        string = (flashcard_set, flashcard_set)
        choices.append(string)
    form = ChooseSetForm(request.form)
    form.Choice.choices = choices

    if request.method == "POST":
        choice = request.form["Choice"]
        session["Chosen Set"] = choice
        logging.debug(f"choice = {choice}")

        if session.get("Origin") == "Study":
            return redirect(url_for("study_set"))
        elif session.get("Origin") == "Edit":
            return redirect(url_for("edit_set"))
    return render_template("choose_set.html", form=form, form_action=form_action)


@app.route("/set_origin_as_study")
def set_origin_as_study():
    session["Origin"] = "Study"
    session["Flag Variable"] = True
    return redirect(url_for("choose_set"))


@app.route("/set_origin_as_edit")
def set_origin_as_edit():
    session["Origin"] = "Edit"
    return redirect(url_for("choose_set"))


@app.route("/study_set", methods=["GET", "POST"])
def study_set():
    last_card = None
    correct = True
    message = None
    study_set_form = StudySetForm(request.form)
    card_set = get_flashcard_set_from_json()

    if session.get("Last Card"):
        last_card = Flashcard.out_of_json(session.get("Last Card"))
        session["card to change in mark_as_correct"] = last_card.into_json()
        logging.debug(f"last card = {last_card}")

    if request.method == "POST":
        if request.is_json:
            # card_to_change = Flashcard.out_of_json(session.get("card to change in mark_as_correct"))
            card_to_change = last_card
            card_to_change.correct_answer()
            logging.debug(f"card to change with AJAX = {card_to_change}")
            card_set = get_flashcard_set_from_json()
            new_card_set = card_set.update_card(card_to_change)
            update_card_sets(new_card_set)
            session["Last Card"] = card_to_change.into_json()
            pass

        elif last_card:
            answer = request.form["Answer"]
            if last_card.definition == answer:
                correct = True
                last_card.correct_answer()
                message = f"That was the correct answer, the answer was {last_card.definition}"
            else:
                last_card.incorrect_answer()
                correct = False
                message = f"That was incorrect. The term was: \n {last_card.term}\n the answer was: \n {last_card.definition}\n Your answer was \n {answer}"
            new_card_set = card_set.update_card(last_card)
            update_card_sets(new_card_set)
            chosen_card = card_set.get_card_to_study()
            term = chosen_card.term
            logging.debug(f"term passed into term=term: {term}")
            study_set_form.Answer.data = ""
            session["Last Card"] = chosen_card.into_json()
    else:
        logging.debug(f"card_set = {card_set}")
        chosen_card = card_set.get_card_to_study()
        term = chosen_card.term
        logging.debug(f"term passed into term=term: {term}")
        session["Last Card"] = chosen_card.into_json()
        study_set_form.Answer.data = ""


    return render_template("study_set.html", study_set_form=study_set_form, term=term, message=message, correct=correct)


@app.route('/debugging_features')
def debugging_features_():
    write_from_f_to_f("flashcard_sets_backup.txt", "flashcard_sets.txt")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
