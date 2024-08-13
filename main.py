from flask import Flask, request, render_template, redirect, url_for, session
from forms import NewSetForm, NewCardForm, ChooseSetForm
import os
from dotenv import load_dotenv
import json
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
    def __repr__(self):
        return self.into_json()

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
            self.learn_score = min(self.learn_score+10, 10)
        else:
            self.learn_score = min(self.learn_score+1, 10)
        self.times_seen = self.times_seen + 1
    def incorrect_answer(self):
        self.learn_score = max(self.learn_score - 1, 0)
        self.times_seen = self.times_seen + 1
    def into_json(self):
        as_dict = self.__dict__
        as_json = json.dumps(as_dict)
        return as_json

    @classmethod
    def out_of_json(cls, json_string):
        data = json.loads(json_string)
        return cls(term=data["term"],definition=data["definition"], learn_score=data["learn_score"], times_seen=data["times_seen"])

def clear_session():
    session.clear()
    session["Set"] = None


def add_new_card_set(card_set):
    with open("flashcard_sets.txt", "r") as file:
        lines = file.readlines()
    with open("flashcard_sets.txt", "w") as file:
        lines.append(card_set)
        for line in lines:
            file.write(line.strip("\n"))
            file.write("\n")

@app.route('/')
def index():
    clear_session()
    return render_template("index.html")

def get_list_of_card_sets():
    names = []
    with open("flashcard_sets.txt", "r") as file:
        lines = file.readlines()
        for line in lines:
            flashcard_set = FlashcardSet.out_of_json(line)
            name = flashcard_set.name
            names.append(name)
    return names

@app.route('/initialise_new_set', methods = ["GET", "POST"])
def initialise_new_set():
    form = NewSetForm(request.form)
    if request.method == "POST":
        name = request.form["Name"]
        session["Flashcard Set"] = FlashcardSet(name, []).into_json()
        return redirect(url_for("add_new_flashcard"))
    return render_template("initialise_new_set.html", form=form)

@app.route("/add_new_flashcard", methods = ["GET","POST"])
def add_new_flashcard():
    new_card_form = NewCardForm(request.form)
    set_json = session.get("Flashcard Set")
    flashcard_set = FlashcardSet.out_of_json(set_json)
    name = flashcard_set.name
    if request.method == "POST":
        term = request.form["Term"]
        definition = request.form["Definition"]
        flashcard = Flashcard(term, definition, 0, 0)
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

@app.route('/study_set', methods = ["GET", "POST"])
def study_set():
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
        print(session.get("Chosen Set"))
        return redirect(url_for("index"))


    return render_template("study_set.html", form=form)

@app.route('/debugging_features')
def debugging_features_():
    print(get_list_of_card_sets())
    return render_template("debugging_features.html")

if __name__ == "__main__":
    app.run(debug=True)