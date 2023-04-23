import openai, os, requests, re, random, json
from json import JSONDecodeError
from enum import Enum
from datetime import datetime, timedelta
from cal_setup import get_calendar_service
from emora_stdm import DialogueFlow, Macro, Ngrams
from typing import Dict, Any, List, Callable, Pattern
import regexutils
model = 'gpt-3.5-turbo'
os.chdir('C:/Users/devin/OneDrive/Documents/GitHub/GymBrOT')
class V(Enum):
    busy_days = 0,  # str
    urgent = 0,
    noturgent = 0,
    important = 0,
    notimportant = 0
#Bug creates a new calendar each time the user runs the bot
#TODO Get free days of week, get free times, find length of time
#Build Calendar
time_manager = {
    'state': 'time_manage_consent',
    '`I want to help you manage your time better? Can I help you with this?`':{
        '[{yes, yeah, yep, ye, yea, yup, yas, ya, for sure, absolutely, definitely, sure, [i, am], [you, {are, know}], right, correct, true, factual, facts, def, always, [i, have], totally}]':{
                '`One of the things that I like to do is set up my priorities into four different categories, based on whether or not they are urgent or whether or not they are important. \n For example, an urgent activity is to submit an essay by 5 pm while a not urgent activity is to schedule a dentist appointment. \n When I think about important activities I think about submitting a maintenance request form to get my bedroom light fixed versus responding to a comment on social media. Does this make sense?`':{
                    '[{yes, yeah, yep, ye, yea, yup, yas, ya, for sure, absolutely, definitely, sure, [i, am], [you, {are, know}], right, correct, true, factual, facts, def, always, [i, have], totally}]':{
                        '`Ok lets try it, what are your really urgent tasks?`':{
                            'state':'findurgent',
                            '#URGENT':{
                                '#URGENTCLASS':{
                                    'yes': {
                                        'state': 'findimportant',
                                        '`Ok now of your not urgent tasks, which of these are important to you?`': {
                                            '#IMPORTANT': {
                                                '#IMPORTANTCLASS': 'end',
                                                'error':'classify'
                                            }

                                        }
                                    },
                                    'no': {
                                        '`Well this is just practice so let\'s go with this example.`': 'findimportant'
                                    },

                                },
                                'error':'findimportant'
                            }
                        }
                    },
                    'error':{
                        '`Ok let\’s just do urgent activities then. What sort of activities do you have on a regular basis that HAVE to immediately get done.`':'findurgent'
                    }

                }
        },
        '[no]':{
                '`Are you sure? I can be really helpful!`':{
                    '[yes]':{
                        '`Ok we can move onto other things then!`':'chatting'
                    },
                    'error':{
                        '`Hmm ok I think we should try for now and lets just see!`':'end'
                    }
                }
        },

    }
}

new_scheduler_transitions = {
    'state': 'scheduler',
    '`So what days and times would work for you to go to the gym for an hour?`':{
        '#DAYS #CREATECALENDAR':{
            'Ok I see, now what times work. Let me find something that works.'
        },
        'error':{

        }
    },
    #'`So based on our conversation today I think I came up with something that works.` #CREATECALENDAR':{
    #    'error':'end'
    #}

}

def get_busy_days(vars: Dict[str, Any]):

    vars[V.busy_days.name][-1] = ''.join(["or ",vars[V.busy_days.name][-1],"s"])
    return 's, '.join(vars[V.busy_days.name])

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

class MacroNLG(Macro):
    def __init__(self, generate: Callable[[Dict[str, Any]], str]):
        self.generate = generate

    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        return self.generate(vars)

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
            print(vars)
        return True





class MacroUrgentClass(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        return 'Hmmm... I would say the following are your urgent tasks:\n'+ "\n".join(vars['urgent'])+"\n\nWhile the following are your not urgent tasks:\n"+ "\n".join(vars['not urgent'])+ "\n\nWhat do you think?"

class MacroImportantClass(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        return 'So I think I got it. I would say the following are your not urgent, important tasks:\n'+ "\n".join(vars['important'])+"\n\nWhile the following are your not urgent, not important tasks tasks:\n"+ "\n".join(vars['not important'])+ "\n\nWhat do you think?"

class MacroCreateCalendar(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        service = get_calendar_service()
        calendar_body = {
            'summary': 'GymBrOT Workout Schedule'
        }
        workout_list = [{"1":"a"},{"2":"b"},{"3":"c"},{"4":"d"},{"5":"e"},{"6":"f"},{"7":"g"},{"8":"h"},{"9":"i"},{"10":"a"},{"11":"b"},{"12":"c"},{"13":"d"},{"14":"e"},{"15":"f"},{"16":"g"},{"17":"h"},{"18":"i"}]
        service.calendars().insert(body=calendar_body).execute()
        descriptions = []

        for i in range(1,len(workout_list)):
            popped = workout_list.pop()
            for key, value in popped.items():
                description = str(key)+":\n"
                description += str(value)+"\n"
                descriptions.append(description)

        d = datetime.now().date()
        print(descriptions)
        for i in range(1,len(vars['DAYS'])):
            recc = []
            day = vars['DAYS'].pop()
            hour = vars['TIMES'].pop()
            for j in range(1,4):
                recc.append(descriptions.pop())
            tomorrow = datetime(d.year, 5, 7+int(day), int(hour))
            start = tomorrow.isoformat()
            end = (tomorrow + timedelta(hours=0.5)).isoformat()
            event_result = service.events().insert(calendarId='primary',
                                                body={
                                                    "summary": "This is a test calendar event",
                                                    "description": '\n'.join(recc),
                                                    "start": {"dateTime": start, "timeZone": 'America/New_York'},
                                                    "end": {"dateTime": end, "timeZone": 'America/New_York'},
                                                    "guestsCanModify": True
                                                }
                                                ).execute()
        return True


macros = {
    'CREATECALENDAR': MacroCreateCalendar(),
    ''
    'BUSYDAYS': MacroNLG(get_busy_days),
    'SETBUSYDAYS': MacroGPTJSON(
        'What days am I busy? Do not include days of the week where I am free.',
         {V.busy_days.name: "Monday"}),
    'URGENT': MacroGPTJSON(
        'Sort these into two categories, urgent and not urgent.',
        {"urgent": ["Going to the hospital","Picking up my brother from school"]}, {"not urgent": ["Watching TV","Going on Instagram"]}),
    'URGENTCLASS': MacroUrgentClass(),
    'IMPORTANT': MacroGPTJSON(
        'Sort these into two categories, important and not important.',
        {"important": ["Going to my brother's graduation", "Picking up my brother from school"]},
        {"not important": ["Watching TV", "Going on Instagram"]}),
    'DAYS': MacroGPTJSON(
        'What days of the week did this person suggest? Return 0 for Sunday, 1 for Monday, 2 for Tuesday, 3 for Wednesday and so on, 4 for Thursday, 5 for Friday, and 6 for Saturday. Also return the time using 24 hour times.',
        {"DAYS": ["0", "1"]},
        {"TIMES": ["10", "22"]}),
    'IMPORTANTCLASS': MacroImportantClass()
   # 'SETDAYS': MacroSetDays()


}

df = DialogueFlow('scheduler', end_state='chatting')
df.load_transitions(new_scheduler_transitions)
df.load_transitions(time_manager)
df.add_macros(macros)

if __name__ == '__main__':
    PATH_API_KEY = 'C:\\Users\\devin\\PycharmProjects\\conversational-ai\\resources/openai_api.txt'
    openai.api_key_path = PATH_API_KEY
    df.run()