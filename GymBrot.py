import openai, os, requests, re, random, json
from typing import Dict, Any, List, Callable, Pattern
from json import JSONDecodeError
from enum import Enum
from emora_stdm import DialogueFlow, Macro, Ngrams
import pickle, os, time, json, requests, re
import regexutils
#os.chdir('C:/Users/devin/OneDrive/Documents/GitHub/GymBrOT')

#This is a test to see if it has pushed
model = 'gpt-3.5-turbo'
def save(df: DialogueFlow, varfile: str):
    df.run()
    d = {k: v for k, v in df.vars().items() if not k.startswith('_')}
    pickle.dump(d, open(varfile, 'wb'))

# This is a good program
def load(df: DialogueFlow, varfile: str):
    d = pickle.load(open(varfile, 'rb'))
    df.vars().update(d)

df = DialogueFlow('start', end_state='end')

if(os.path.exists('resources/gymbrot.pkl')):
    load(df, 'resources/gymbrot.pkl')

class V(Enum):
    INITMOOD = '0',
    ACTIVITYLEVEL = '0',
    FITNESSLEVEL = '0',
    ACTIVITYFREQ = '0',
    PREFACTIVITY = '0',
    WHYNOT = '0'# str


intro_transitions = {
    'state':'start',
        '#VISITS`Hey bro, I’m GymBrOT, but you can call me Gym for short! You feelin pumped today?!?!`':{
            '#INITMOOD #SETINITMOOD': {
                '`That’s what’s up bro!\n I bet you’ve been getting some sick gains recently, am I right?`': {
                    'state': 'offer',
                    '[yes]': {
                        '`Nice bro! Don’t think I didn’t notice those gains!\n`': 'name'
                    },
                    '[no]': {
                        '`Bro.. you got to get on that, but don’t worry bro I can help with that!\n`': 'name'
                    }
                },
                '#IF($INITMOOD=negative)`That’s tough bro. You know what I heard?\n Going to the gym is like scientifically proven to help improve your mood or whatever. Have you been workin on your gains?`': 'offer',
                '#IF($INITMOOD=neutral)`Hey bro, that’s better than what the last guy told me.\n You know what I do when I feel off, hit the gym! Have you been workin on your gains?`': 'offer'
     }

    }
}

name_transitions = {
    'state': 'name',
    '`Wait bro, I almost forgot. Like, what do people call you, dude?`': {
        '#GETNAME': {
            '#IF($RETURNUSER=True)`Hey bro, how\'s the gains been going?`': 'check-up',
            '#IF($RETURNUSER=False)`I don\'t think we\'ve met before. Let me learn a little bit more about you...\n`': 'new_user'
        }
    }
}

newuser_transitions= {
    'state': 'new_user',
    '`So are you a gym rat, or nah?`':{
        '#ACTIVITYLEVEL #GETACTIVITYLEVEL':{
                '#IF($ACTIVITYLEVEL=confused)`Sorry bro! I forget that not everyone knows gym lingo like me.\n A gym rat just like spends their free time in the gym. Like me!\n If you ever need me to explain something like that, just ask bro.`': {
                    'error':{
                        'Any time bro. I’m like your spotter but for knowledge.':'new_user'
                    }
                },
                '#IF($ACTIVITYLEVEL=never)`Test`': 'new_user'
        }
    },
    '#GATE`Oh, I got you. Helping fresh gym rats figure out their routine gets me pumped!\n On a scale of 1-10, how swole are you?`':{
        '#FITNESSLEVEL #GETFITNESSLEVEL':{
            '$FITNESSLEVEL':'end'
        }
    },
    '#GATE`That’s what’s up! I love meeting other bros like me who are dedicated to the gains.\n How often do you make it to the gym?`':{
        '#ACTIVITYFREQ #GETACTIVITYFREQ':{
            '$GETACTIVITYFREQ':'end'
        }
    },
    '#GATE`Bro to bro, I gotta know - how have you been getting those sweet sweet gains?`': {
        '#PREFACTIVITY #GETPREFACTIVITY':{
            '$PREFACTIVITY':'end'
        }
    },
    '#GATE`What? Gains are life, bro. Why aren\'t you hitting the gym?`': {
        '#WHYNOT #GETWHYNOT':{
            '$WHYNOT':'end'
        }
    }
}


checkup_transitions= {
    'state': 'workout_progress_feelings',
    #Sentiment analysis to the effect of: has this user had any problems in the gym? Is so what kind of problem? and set the variable problem to the issue.
    '`Ok.`':'end'
}



class MacroGetName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        r = re.compile(r"([a-z']+)(?:\s([a-z']+))?")
        m = r.search(ngrams.text())
        if m is None: return False

        firstname, lastname = None, None
        completeName = ""
        if m.group(2):
            firstname = m.group(1)
            lastname = m.group(2)
            completeName = firstname + " " + lastname
        else:
            firstname = m.group()
            completeName = firstname

        if completeName in vars['NAME']:
            vars['RETURNUSER'] = 'True'
            vars['NAME'].append(completeName)
        else:
            vars['RETURNUSER'] = 'False'
            vars['NAME'].append(completeName)
        return True

class MacroVisits(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        vn = 'VISITS'
        if vn not in vars:
            vars[vn] = 1
            vars['NAME'] = []
            vars['RETURNUSER'] = False
            vars['MUSIC'] = ["Thats Amore","Whispering Pines","Good Guy","Happy","Levitating","Bitch Better Have My Money","Lucid Dreams","Autumn Almanac","Shape of You"]
            vars['MOVIE'] = ["Team America: World Police","Feast of Love","Terminator 3: Rise of the Machines","2001: A Space Odyssey","Rush Hour 3","The Grudge","Horrible Bosses","Blade: Trinity","The Help"]
            vars['PREVREC'] = {}
        else:
            count = vars[vn] + 1
            vars[vn] = count


class MacroGreeting(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        vn = 'GREETING'
        if vn not in vars:
            vars[vn] = ["How should I refer to you name wise?"
                ,"During this conversation, what should I call you?","And your name is?"
                ,"What name should I use to refer to you?"
                ,"What should I call you?","What is your name?"
                ,"To whom do I have the pleasure of speaking with?"
                ,"What should I call you for future encounters?"]
            return vars[vn].pop()
        elif len(vars[vn]) == 0:
            return "Wow a repeat offender? What is your name again?"
        else:
            return vars[vn].pop()

class MacroTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        current_time = int(time.strftime("%H"))
        output = ""
        if current_time in range (4, 11):
            output = "It's honestly too early for me to interact with you, but fine..."
        elif current_time >= 23 or current_time < 4:
            output = "A night owl, I see that we are on the same wavelength."
        elif current_time in range (11, 18):
            output = "Isn\'t this business hours? Shouldn\'t you be working?"
        else:
            output = "As the day comes to a close, how did your day go today?"
        return output

class MacroWeather(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        url = 'https://api.weather.gov/gridpoints/FFC/52,88/forecast'
        r = requests.get(url)
        d = json.loads(r.text)
        periods = d['properties']['periods']
        today = periods[0]
        output = ""
        fore = today['shortForecast'].lower()
        if "sunny" in fore:
            output = "a sunny day outside. Hooray!\n"
        elif "rain" in fore:
            output = "a rainy day outside. Boo!\n"
        elif "cloudy" in fore:
            output = "a cloudy day outside. I'm feeling sleepy.\n"
        elif "clear" in fore:
            output = "a clear day outside. Maybe we should go outside.\n"
        else:
            output = "a crappy day outside. Maybe we should stay inside.\n"

        return output


class MacroNameCheck(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):

        if vars['RETURNUSER'] :
           output = "Last time I recommended " + vars['PREVREC'][vars['NAME'][-1]] +". How did you enjoy it?"

        else:
            output = "It\'s nice to meet you "+ vars['NAME'][-1] +". Were you interested in a movie or music reccommendation?"
        return output

def get_ACTIVITYLEVEL(vars: Dict[str, Any]):
    vars['ACTIVITYLEVEL'] = vars[V.ACTIVITYLEVEL.name][random.randrange(len(vars[V.ACTIVITYLEVEL.name]))]
    print(vars['ACTIVITYLEVEL'])
    return

def get_FITNESSLEVEL(vars: Dict[str, Any]):
    vars['FITNESSLEVEL'] = vars[V.FITNESSLEVEL.name][random.randrange(len(vars[V.FITNESSLEVEL.name]))]
    print(vars['FITNESSLEVEL'])
    return

def get_ACTIVITYFREQ(vars: Dict[str, Any]):
    vars['ACTIVITYFREQ'] = vars[V.ACTIVITYFREQ.name][random.randrange(len(vars[V.ACTIVITYFREQ.name]))]
    print(vars['ACTIVITYFREQ'])
    return

def get_PREFACTIVITY(vars: Dict[str, Any]):
    vars['PREFACTIVITY'] = vars[V.PREFACTIVITY.name][random.randrange(len(vars[V.PREFACTIVITY.name]))]
    print(vars['PREFACTIVITY'])
    return

def get_WHYNOT(vars: Dict[str, Any]):
    vars['WHYNOT'] = vars[V.WHYNOT.name][random.randrange(len(vars[V.WHYNOT.name]))]
    print(vars['WHYNOT'])
    return


def get_INITMOOD(vars: Dict[str, Any]):
    ls = vars[V.INITMOOD.name]
    return ls[random.randrange(len(ls))]

class MacroRec(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if  "music" in args[0]:
            if len(vars["MUSIC"]) >= 1:
                rec = vars["MUSIC"].pop()
                vars['PREVREC'][vars['NAME'][-1]] = rec
            else:
                "I have given you all that I have! You should listen to Shape of You again!"
                rec = "Shape of You"
        else:
            if len(vars["MOVIE"]) >= 1:
                rec = vars["MOVIE"].pop()
                vars['PREVREC'][vars['NAME'][-1]] = rec
            else:
                "I have given you all that I have! You should listen to Shape of You again!"
                rec = "The Help"

class MacroSETINITMOOD(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        vars['INITMOOD'] = get_INITMOOD(vars)
        return


        return rec
def gpt_completion(input: str, regex: Pattern = None) -> str:
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': input}]
    )
    output = response['choices'][0]['message']['content'].strip()

    if regex is not None:
        m = regex.search(output)
        output = m.group().strip() if m else None

    return output

class MacroGPTJSON(Macro):
    def __init__(self, request: str, full_ex: Dict[str, Any], empty_ex: Dict[str, Any] = None, set_variables: Callable[[Dict[str, Any], Dict[str, Any]], None] = None):
        self.request = request
        self.full_ex = json.dumps(full_ex)
        self.empty_ex = '' if empty_ex is None else json.dumps(empty_ex)
        self.check = re.compile(regexutils.generate(full_ex))
        self.set_variables = set_variables
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        examples = f'{self.full_ex} or {self.empty_ex} if unavailable' if self.empty_ex else self.full_ex
        prompt = f'{self.request} Respond in the JSON schema such as {examples}: {ngrams.raw_text().strip()}'
        output = gpt_completion(prompt)
        if not output: return False

        try:
            d = json.loads(output)
        except JSONDecodeError:
            print(f'Invalid: {output}')
            return False

        if self.set_variables:
            self.set_variables(vars, d)
        else:
            vars.update(d)
            print(output)
        return True

class MacroNLG(Macro):
    def __init__(self, generate: Callable[[Dict[str, Any]], str]):
        self.generate = generate

    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        return self.generate(vars)

macros = {
    'VISITS': MacroVisits(),
    'ACTIVITYLEVEL':MacroGPTJSON(
        'How often does this person go to the gym?',
        {V.ACTIVITYLEVEL.name: ["yes", "never", "occasionally","excercise other places", "confused"]}),
    'FITNESSLEVEL': MacroGPTJSON(
        'How swole is this person on a scale of 0 through 10 with 10 being the highest?',
        {V.FITNESSLEVEL.name: ["1", "2", "confused"]}),
    'ACTIVITYFREQ': MacroGPTJSON(
        'How many times a week does a person go to the gym?',
        {V.ACTIVITYFREQ.name: ["once", "twice", "seven"]}),
    'PREFACTIVITY': MacroGPTJSON(
        'What activity does the person do to exercise?',
        {V.PREFACTIVITY.name: ["lifting", "cardio", "confused","nothing"]}),
    'WHYNOT': MacroGPTJSON(
        'Why does this person not go to the gym?',
        {V.WHYNOT.name: ["judgement", "safety", "busy","disability"]}),
    'GETNAME': MacroGetName(),
    'SETINITMOOD': MacroSETINITMOOD(),
    'GETINITMOOD': MacroNLG(get_INITMOOD),
    'GETACTIVITYLEVEL': MacroNLG(get_ACTIVITYLEVEL),
    'GETFITNESSLEVEL': MacroNLG(get_FITNESSLEVEL),
    'GETACTIVITYFREQ': MacroNLG(get_ACTIVITYFREQ),
    'GETPREFACTIVITY': MacroNLG(get_PREFACTIVITY),
    'GETWHYNOT': MacroNLG(get_WHYNOT),
    'INITMOOD': MacroGPTJSON(
        'Is this user positive, negative, or neutral?',
        {V.INITMOOD.name: ["positive", "negative", "neutral"]})
}


df.load_transitions(intro_transitions)
df.load_transitions(checkup_transitions)
df.load_transitions(name_transitions)
df.load_transitions(newuser_transitions)
df.add_macros(macros)



if __name__ == '__main__':
    PATH_API_KEY = 'C:\\Users\\devin\\PycharmProjects\\conversational-ai\\resources\\openai_api.txt'
    openai.api_key_path = PATH_API_KEY
    save(df, 'resources/gymbrot.pkl')

