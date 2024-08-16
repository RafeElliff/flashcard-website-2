from flask import Flask, request, render_template, redirect, url_for, session
from forms import NewSetForm, NewCardForm, ChooseSetForm, StudySetForm
import os
from dotenv import load_dotenv
import json
import random

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv("flask_secret_key")

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
        for card in self.flashcards_list:
            valid_cards.append(card)
            card = Flashcard.out_of_json(card)
            weightings.append(11 - (card.learn_score))
        choices =  random.choices(valid_cards, weightings, k=1)
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


def is_valid_json(string):
    try:
        json.loads(string)
        return True
    except:
        return False


def get_flashcard_set_from_json():
    flashcard_sets = None
    chosen_set = session.get("Chosen Set")
    with open("flashcard_sets.txt", "r") as file:
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
    with open("flashcard_sets.txt", "r") as file:
        lines = file.readlines()
    with open("flashcard_sets.txt", "w") as file:
        lines.append(card_set)
        for line in lines:
            file.write(line.strip("\n") + "\n")

def get_list_of_card_sets():
    names = []
    with open("flashcard_sets.txt", "r") as file:
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
    lines = read_lines("flashcard_sets.txt")
    for line in lines:
        set_on_line = json.loads(line)
        if set_on_line["name"].strip("") == chosen_set_name.strip(""):
            index_to_update = index
        index = (index+1)
    if index_to_update is not None:
        lines[index_to_update] = new_card_set_dict
    with open("flashcard_sets.txt", "w") as file:
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
@app.route('/')
def index():
    initialise()
    return render_template("index.html")


@app.route('/initialise_new_set', methods=["GET", "POST"])
def initialise_new_set():
    form = NewSetForm(request.form)
    if request.method == "POST":
        name = request.form["Name"]
        session["Flashcard Set"] = FlashcardSet(name, []).into_json()
        return redirect(url_for("add_new_flashcard"))
    return render_template("initialise_new_set.html", form=form)


@app.route("/add_new_flashcard", methods=["GET", "POST"])
def add_new_flashcard():
    new_card_form = NewCardForm(request.form)
    set_json = session.get("Flashcard Set")
    flashcard_set = FlashcardSet.out_of_json(set_json)
    name = flashcard_set.name
    if request.method == "POST":
        term = request.form["Term"]
        definition = request.form["Definition"]
        flashcard = Flashcard(term, definition, 3, 0)
        flashcard_set.add_new_card(flashcard)
        session["Flashcard Set"] = flashcard_set.into_json()

        return redirect(url_for("add_new_flashcard"))

    return render_template("add_new_flashcard.html", name=name, form=new_card_form)


@app.route("/finish_set")
def finish_set():
    finished_set = session.get("Flashcard Set")
    add_new_card_set(finished_set)
    return redirect(url_for("index"))


@app.route('/edit_set')
def edit_set():
    return render_template("edit_set.html")


@app.route('/choose_set', methods=["GET", "POST"])
def choose_set():
    choices = []
    flashcard_sets = get_list_of_card_sets()
    for flashcard_set in flashcard_sets:
        string = (flashcard_set, flashcard_set)
        choices.append(string)
    form = ChooseSetForm(request.form)
    form.Choice.choices = choices

    if request.method == "POST":
        choice = request.form["Choice"]
        session["Chosen Set"] = choice
        return redirect(url_for("study_set"))

    return render_template("choose_set.html", form=form)


@app.route("/mark_as_correct", methods=["GET", "POST"])
def mark_as_correct():
    card_to_change = Flashcard.out_of_json(session.get("card to change in mark_as_correct"))
    card_to_change.correct_answer()
    card_set = get_flashcard_set_from_json()
    new_card_set = card_set.update_card(card_to_change)
    update_card_sets(new_card_set)
    session["Changed Card"] = card_to_change.into_json()
    return redirect(url_for("study_set"))

@app.route("/study_set", methods = ["GET", "POST"])
def study_set():
    last_card = None
    correct = True
    message = None
    study_set_form = StudySetForm(request.form)
    card_set = get_flashcard_set_from_json()

    if session.get("Last Card"):
        last_card = Flashcard.out_of_json(session.get("Last Card"))
        session["card to change in mark_as_correct"] =last_card.into_json()
        if session.get("Changed Card"):
            session["Changed Card"] = None
            last_card = Flashcard.out_of_json(session.get("Changed Card"))
    if request.method == "POST" and last_card:
        answer = request.form["Answer"]
        if last_card.definition == answer:
            correct = True
            last_card.correct_answer()
            message = f"That was the correct answer, the answer was {last_card.definition}"
        else:
            last_card.incorrect_answer()
            correct = False
            message = f"That was incorrect, the answer was: \n {last_card.definition}\n Your answer was \n {answer}"
        new_card_set = card_set.update_card(last_card)
        update_card_sets(new_card_set)
        redirect(url_for("study_set"))

    chosen_card = card_set.get_card_to_study()
    term = chosen_card.term
    session["Last Card"] = chosen_card.into_json()



    return render_template("study_set.html", study_set_form=study_set_form, term=term, message = message, correct = correct)

@app.route('/debugging_features')
def debugging_features_():
    card_set = get_flashcard_set_from_json()
    choice = card_set.get_card_to_study()

    return render_template("debugging_features.html")

if __name__ == "__main__":
    app.run(debug=True)
