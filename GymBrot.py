import openai, os, requests, re, random, json
from typing import Dict, Any, List, Callable, Pattern
from json import JSONDecodeError
from enum import Enum
from emora_stdm import DialogueFlow, Macro, Ngrams
import pickle, os, time, json, requests, re
import regexutils
#os.chdir('C:/Users/devin/OneDrive/Documents/GitHub/GymBrOT')
os.chdir('/Users/kristen/PycharmProjects/GymBrOT')
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
    INITMOOD = 1,
    ACTIVITYLEVEL = 2,
    FITNESSLEVEL = 3,
    ACTIVITYFREQ = 4,
    PREFACTIVITY = 5,
    WHYNOT = 6


intro_transitions = {
    'state':'start',
        '#VISITS`Hey bro, I’m GymBrOT, but you can call me Gym for short! You feelin pumped today?!?!`':{
            '#INITMOOD #SETINITMOOD': {
                '`That’s what’s up bro!\n I bet you’ve been getting some sick gains recently, am I right?`': {
                    'state': 'offer',
                    '[{yes, yeah, yep, ye, yea, yup, yas, ya, for sure, absolutely, definitely, sure, [i, am], [you, {are, know}], right, correct, true, factual, facts, def, always, [i, have], totally}]': {
                        '`Nice bro! Don’t think I didn’t notice those gains!\n`': 'name'
                    },
                    '[{no, nope, nah, not, dont, [im, not], [youre, {wrong, not}], never, negative, havent}]': {
                        '`Bro.. you got to get on that, but don’t worry bro I can help with that!\n`': 'name'
                    },
                    'error': {
                        '`Hold up bro, I couldn\'t catch your vibe. Can you say that again?`': 'offer'
                    }
                },
                '#IF($INITMOOD=negative)`That’s tough bro. You know what I heard?\n Going to the gym is like '
                'scientifically proven to help improve your mood or whatever. Have you been workin on your gains?`':
                    'offer',
                '#IF($INITMOOD=neutral)`Hey bro, that’s better than what the last guy told me.\n You know what I do '
                'when I feel off, hit the gym! Have you been workin on your gains?`': 'offer'
     }

    }
}

name_transitions = {
    'state': 'name',
    '`Wait bro, I almost forgot. Like, what do people call you, dude?`': {
        '#GETNAME': {
            'state':'got_name',
            '#IF($RETURNUSER=True)`Hey bro, how\'s the gains been going?`': 'check-up',
            '#IF($RETURNUSER=False)`I don\'t think we\'ve met before. Let me learn a little bit more about you...\n`': 'new_user'
        },
        'error':{
            'Wait bro... are you sure that\'s your name? Like, what do people call you?': {
                '#GETNAME':{
                    '': 'got_name'
                },
                'error':'end'
            }
        }
    }
}

newuser_transitions= {
    'state': 'new_user',
    '`So are you a gym rat, or nah?`':{
        '#ACTIVITYLEVEL #GETACTIVITYLEVEL':{
            '#IF($ACTIVITYLEVEL=confused)`Sorry bro! I forget that not everyone knows gym lingo like me.\n A gym rat '
            'just like spends their free time in the gym. Like me!\n If you ever need me to explain something like '
            'that, just ask bro.`': {
                'error':{
                    '`Any time bro. I’m like your spotter but for knowledge.`':'new_user'
                }
            },
            '#IF($ACTIVITYLEVEL=yes) `Nice… I’m not sure why I asked, because just by looking at the size of your` '
            '#RANDOM_MUSCLE `I could tell. I just hit legs earlier today… can you tell?`': {
                '[{yes, yeah, yep, ye, yea, yup, yas, ya, for sure, absolutely, definitely, sure, [you, know], right, '
                'correct, true, factual, facts, def, always, [i, can], totally}]': {
                    '`Thanks bro I work hard to look this good… and be healthy!`':'new_user'
                },
                '[{no, nope, nah, not, dont, [im, not], [youre, {wrong, not}], never, negative, havent}]': {
                    '`Aw bro… we should be hyping each other up, not putin each other down. I thought you\'d know '
                    'that.`':'new_user'
                },
                '[{computer, bot, metal, code}]':{
                    '`What do you mean I\'m a computer… Error 404: Incompatible hardware detected. System shutoff '
                    'initiated… hahaha just messing with you bro. Just because I\'m a computer doesn\'t mean I don\'t '
                    'have a healthy lifestyle and sick muscles.`':'new_user'
                }

                },
            '#IF($ACTIVITYLEVEL=no)`Hey bro, I don\'t judge. But if you don\'t mind me asking, why don\'t you go to '
            'the gym?`':'whynot',
            '#IF($ACTIVITYLEVEL=maybe) `Hey bro, I don’t judge. Any activity is better than no activity. Do you feel '
            'like you go to the gym as often as you\'d like?`': {
                '[{yes, yeah, yep, ye, yea, yup, yas, ya, for sure, absolutely, definitely, sure, [you, know], right, '
                'correct, true, factual, facts, def, always, [i, can], totally, enough, often, like}]': {
                    '`That’s what\'s up then bro! It\'s about whatever works best for you.`':'new_user'
                },
                '[{no, nope, nah, not, dont, [im, not], never, negative}]': {
                    '`It happens bro, sometimes life and just stuff gets in the way. But if you don’t mind me asking, '
                    'why aren’t you hitting the gym as often as you/’d like?`':'whynot'
                },
                'error':{
                    '`I gotchu bro.`':'new_user'
                }

            },
            '`felt that, bro`':'new_user'
            },
        'error':{
            '`Oh. Gotchu bro.`':'new_user'
        }
    },
    '#GATE`Helping fresh gym rats figure out their routine gets me pumped!\n On a scale of 1-10, how swole are you?`':{
        'state':'getting_level',
        '#FITNESSLEVEL #GETFITNESSLEVEL':{
            '#IF($FITNESSLEVEL=0) `I gotchu bro. Everyone starts from somewhere. Is there a reason why you aren\'t hitting the gym?`': 'whynot',
            '#IF($FITNESSLEVEL=1) `Ok, ok! I hope you\'re ready to get leveled up, because being swole is the #1 way to be fulfilled ('
                'like, this is not a real fact bro. Don\'t come for me, I just like being swole.) \n But like, '
                'why aren\'t you hitting the gym?`':'whynot',
            '#IF($FITNESSLEVEL=2)': 'notswole',
            '#IF($FITNESSLEVEL=3)': 'notswole',
            'state': 'mid',
            '#IF($FITNESSLEVEL=4)`Ok, I see you! Are you trying to level up, dude?`': {
                '{yes, yeah, yep, ye, yea, yup, yas, ya, for sure, absolutely, definitely, sure, [i, am], [you, are], right, correct, true, factual, facts, def, always, [i, have], know}':{
                        '`ok! so what\'s holding you back from leveling up, bro?': 'whynot'
                    },
                    '{no, nope, nah, not, dont, [im, not], [youre, {wrong, not}], never, negative, havent}':{
                        '`I feel you, dude - we can\'t all be super swole, but I\'m pumped that you\'re maintaining those gains!`':'new_user'
                    }
            },

            '#IF($FITNESSLEVEL=5)': 'mid',
            '#IF($FITNESSLEVEL=6)': 'mid',
            '#IF($FITNESSLEVEL=7)': 'mid',
            'state':'swole', '#IF($FITNESSLEVEL=8)`Hell yeah, a bro who knows that gains are life!`': 'new_user',
            '#IF($FITNESSLEVEL=9)': 'swole',
            '#IF($FITNESSLEVEL=10)': 'swole',
            '#IF($FITNESSLEVEL=confused)': {
                '#GATE `Sorry bro, I forget that not everyone is fluent in gym. \n Swole is basically just like, '
                'how fit you are. How much you can lift, how long you can run, how fast, max/min, that kinda stuff. '
                'Now that you know, how swole are you, from 1-10?`':'getting_level',
                '`That\'s ok bro. We can talk more about your swoleness later.`': 'new_user', 'score': 0.1
            },
            '`Ok bro! Good to know.`':'new_user'
        },
        'error':{
        '`Ok bro! Good to know.`':'new_user'
        }
    },

    '#GATE`That’s what’s up! I love meeting other bros like me who are dedicated to the gains.\n How often do you make it to the gym?`':{
        '#ACTIVITYFREQ':{
            '#IF($ACTIVITYFREQ=never) `Dude... we gotta change that! Gains are life, bro. Why aren\'t you hitting the gym?`': {
                'state': 'whynot',
                '#WHYNOT #GETWHYNOT':{
                    '$WHYNOT':'end'
                }
            },
            '#IF($ACTIVITYFREQ=low)`Hmm... you definitely might want to hit the gym, more, dude. A healthy lifestyle comes from building healthy habits.`':'whynot',
            '#IF($ACTIVITYFREQ=mid)`Ok, I see you! Gettin those gains in!`':'new_user',
            '#IF($ACTIVITYFREQ=high)`Yoooo, you should be my full-time lifting buddy!`': 'new_user',
            '#IF($ACTIVITYFREQ=swole) `Dude. Your gains must be legendary! The grind never stops frfr`': 'new_user',
            'Oh I gotchu bro':'new_user'
        }
    },
    '#GATE`Bro to bro, I gotta know - how have you been getting those sweet sweet gains?`': {
        '#PREFACTIVITY #GETPREFACTIVITY': {
            '`Yo dude,` $PREFACTIVITY `is sick! Personally, I love hitting the gym on leg day. \n I get a pump in at least twice per day... \n but my full time job and favorite mental workout is being a personal trainer!`': 'new_user'
        },
        'error':{
            '`Damn bro.`':'new_user'
        }
    },
    'error' : {
        'I see I see':'new_user'
    }

}
emotional_transitions = {


}

workout_planning_transitions ={
    'state': 'formulate_plan'

}

normal_dialogue_transitions = {
    'state':'chatting'

}

checkup_transitions= {
    'state': 'workout_progress_feelings',
    #Sentiment analysis to the effect of: has this user had any problems in the gym? Is so what kind of problem? and set the variable problem to the issue.
    '`Ok.`':'end'
}


global_transitions={
    '[{birthday, birth, day, annual, celebration}]':{
        '`whoa dude. like. congrats!!!!`':'chatting'
    },
    '[{emergency, [immediate, danger]}]':{
        '`wait, dude. Don\'t tell me. call emergency services or talk to someone who can help you in person. I\'m not capable of calling for help or giving you advice about this.`':'end'
    },
    '[{suicide, [self, {harm, harming}], [killing, myself]}]':{
        '`hey. You\'re my best gym buddy, but also I\'m just a chatbot. I\'m not capable of providing you the support '
        'you need right now. If you need someone to talk to, call 988 or 1-800-273-8255. You\'re not alone.`':'end'
    },
    '[{[Im, in, love, with, you], [I, want, you], [I, want, to, be, your, {boyfriend, girlfriend}], [I, have, a, crush, on, you]}]':{
        '`whoa bro. I love you in a bromance kinda way. I\'m just a chatbot, and I don\'t feel emotions like romantic '
        'love (even tho you\'re my gym bro!)`':'chatting'
    },
    '[[help, make, workout, plan], [help, workout, {plan, planning}]':'formulate_plan'
}


class MacroGetName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        r = re.compile(r"(?:(?:(?:you can |my friends )?call me)|(?:it(s| is))|(?:i(m| am))|(?:my name is)|(?:i go by))?(?:^|\s)(mr|mrs|ms|dr)?(?:^|\s)([a-z']+)(?:\s([a-z']+))?")
        m = r.search(ngrams.text())
        if m is None: return False

        title, firstname, lastname = None, None, None
        completeName = ""
        if m.group(3):
            if m.group(4) and not m.group(5):
                title = m.group(3)
                lastname = m.group(4)
                completeName = title + " " + lastname
            elif m.group(5):
                title = m.group(3)
                firstname = m.group(4)
                lastname = m.group(5)
                completeName = title + " " + firstname + " " + lastname
            else:
                title = m.group(3)
                completeName = title
        elif m.group(5):
            firstname = m.group(4)
            lastname = m.group(5)
            completeName = firstname + " " + lastname
        else:
            firstname = m.group(4)
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
            vars[V.INITMOOD] = []
            vars[V.ACTIVITYLEVEL] = []
            vars[V.ACTIVITYFREQ] = []
            vars[V.FITNESSLEVEL] = []
            vars[V.PREFACTIVITY] = []
        else:
            count = vars[vn] + 1
            vars[vn] = count


class MacroGreeting(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        vn = 'GREETING'
        if vn not in vars:
            vars[vn] = ["You feelin pumped today?!?!"
                ,"Are you ready to hit the gym???","Are we gonna lift together today or nah?!?"
                ,"Are you pumped or are you pumped??"
                ,"Today\'s hella good, because I\'m pumped! Are you with me?"]
            return vars[vn].pop()
        elif len(vars[vn]) == 0:
            return "You feelin pumped today?!?!"
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
    vars['ACTIVITYLEVEL'] = vars[V.ACTIVITYLEVEL.name]
    print(vars['ACTIVITYLEVEL'])
    return

def get_FITNESSLEVEL(vars: Dict[str, Any]):
    vars['FITNESSLEVEL'] = vars[V.FITNESSLEVEL.name]
    print(vars['FITNESSLEVEL'])
    return

def get_ACTIVITYFREQ(vars: Dict[str, Any]):
    vars['ACTIVITYFREQ'] = vars[V.ACTIVITYFREQ.name]
    print(vars['ACTIVITYFREQ'])
    return

def get_PREFACTIVITY(vars: Dict[str, Any]):
    vars['PREFACTIVITY'] = vars[V.PREFACTIVITY.name]
    print(vars['PREFACTIVITY'])
    return

def get_WHYNOT(vars: Dict[str, Any]):
    vars['WHYNOT'] = vars[V.WHYNOT.name]
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
        print(output)
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
class MacroRandomMuscle(Macro):
    """Fix"""
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        with open('/Users/kristen/PycharmProjects/GymBrOT/resources/ontology_workouts.json') as ont_file:
            ont_file = ont_file.read()
            parsed_file = json.loads(ont_file)
            musc_groups = parsed_file["ontology"]["muscle groups"]
            group = musc_groups[random.randrange(len(musc_groups))]
            group = parsed_file["ontology"][group]
            musc = group[random.randrange(len(group))]
            return musc
macros = {
    'VISITS': MacroVisits(),
    'ACTIVITYLEVEL':MacroGPTJSON(
        'Is this person agreeing that they are a gym rat? Respond with yes, no, or maybe, unless they are confused by the question. In that case they are "confused"',
        {V.ACTIVITYLEVEL.name: "yes"}, {V.ACTIVITYLEVEL.name:"N/A"}),
    'FITNESSLEVEL': MacroGPTJSON(
        'How physically fit/swole is this person on a scale of 0 through 10 with 10 being the highest?',
        {V.FITNESSLEVEL.name:"1"},{V.FITNESSLEVEL.name:"N/A"} ),
    'ACTIVITYFREQ': MacroGPTJSON(
        'How many times a week does a person go to the gym, with 0 being never, 1 or 2 being low, less than 5 being mid, less than 8 being high, and greater than 8 being swole. They may go more than once per day',
        {V.ACTIVITYFREQ.name: "never"}, {V.ACTIVITYFREQ.name:"N/A"}),
    'PREFACTIVITY': MacroGPTJSON(
        'What activity does the person do to exercise?',
        {V.PREFACTIVITY.name: "lifting"}, {V.PREFACTIVITY.name:"N/A"}),
    'WHYNOT': MacroGPTJSON(
        'Why does this person not go to the gym?',
        {V.WHYNOT.name: ["judgement", "safety", "busy","disability"]}, {V.WHYNOT.name:[]}),
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
        {V.INITMOOD.name: ["positive", "negative", "neutral"]}),
    'GREETING': MacroGreeting,
    'RANDOM_MUSCLE': MacroRandomMuscle()
}


df.load_transitions(intro_transitions)
df.load_transitions(checkup_transitions)
df.load_transitions(name_transitions)
df.load_transitions(newuser_transitions)
df.add_macros(macros)



if __name__ == '__main__':
    #PATH_API_KEY = 'C:\\Users\\devin\\PycharmProjects\\conversational-ai\\resources\\openai_api.txt'
    PATH_API_KEY = '/Users/kristen/PycharmProjects/GymBrOT/resources/api.txt'
    openai.api_key_path = PATH_API_KEY
    save(df, 'resources/gymbrot.pkl')

