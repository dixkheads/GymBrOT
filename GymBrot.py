from typing import Dict, Any, List
from emora_stdm import DialogueFlow, Macro, Ngrams
import pickle, os, time, json, requests, re
os.chdir('C:\\Users\\devin\\PycharmProjects\\conversational-ai')
#This is a test to see if it has pushed
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

intro_transitions = {
    'state': 'start',
    '#VISITS`Yo bro, who\'s on the other end of this convo today?`': {
        '#GETNAME':{
            '#IF($RETURNUSER=True)`Hey bro, how\'s it been going?`': {
                #Once we have sentiment analysis, analyze user response and set mood to good or bad to continue on dialogue path
                #'#IF($MOOD=Good)`That\'s, what\'s up bro. How are the gains going?`'
                '[good]':{
                    '`That\'s, what\'s up bro. How are the gains going?`':'workout_progress_feelings`'
                },
                '[bad]':{
                    '`That\'s tuff bro, sounds like you need to work on your gains. Have you had any problems in the gym recently?`':'workout_progress_feelings'
                }
            },
            '#IF($RETURNUSER=False)`I don\'t think we\'ve met before, how is it going bro?`': 'end'
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

macros = {
    'VISITS': MacroVisits(),
    #'GREETING': MacroGreeting(),
    #'TIME': MacroTime(),
    #'WEATHER': MacroWeather(),
    'GETNAME': MacroGetName() #,
    #'NAMECHECK': MacroNameCheck(),
    #'REC': MacroRec(),
    #'PREVREC': MacroPrevRec()
}


df.load_transitions(intro_transitions)
df.load_transitions(checkup_transitions)
df.add_macros(macros)



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

        return rec




if __name__ == '__main__':
    save(df, 'resources/gymbrot.pkl')

