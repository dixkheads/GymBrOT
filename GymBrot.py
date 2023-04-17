import openai, os, requests, re, random, json
from typing import Dict, Any, List, Callable, Pattern
from json import JSONDecodeError
from enum import Enum
from emora_stdm import DialogueFlow, Macro, Ngrams
import pickle, os, time, json, requests, re
import regexutils
#os.chdir('C:/Users/devin/OneDrive/Documents/GitHub/GymBrOT')
#os.chdir('/Users/kristen/PycharmProjects/GymBrOT')
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


consent_transitions = {
    'state': 'consent',
    '`Hello Gym bros! We\'re excited you\'re here and want us to join your fitness journey. Before we begin,`'
    '`in case of an emergency, or if you are in immediate danger, please contact the appropriate authorities or emergency`'
    '`services immediately. Additionally, while our chatbot can provide helpful information and guidance, it is not a`'
    '`substitute for professional medical advice or guidance from a qualified fitness trainer.`'
    '`Please listen to your body and use your best judgment while exercising. If you are experiencing pain or discomfort`'
    '`while exercising, please stop immediately and seek guidance from a certified fitness professional.`'
    '`With that all out of the way, if you understand and wish to continue, please type \"I understand\" now.`': {
        '[I understand]': {
            '`Great! Thank you and best of luck on your fitness journey!': 'start'
        },
        'error': 'end'
    }
}

intro_transitions = {
    'state':'start',
        '#VISITS`Hey bro, I’m GymBrOT, but you can call me bro, dude, homie, whatever you feel, you feel? Anyway dude, you ready to grind today?!?!`':{
            '#INITMOOD #SETINITMOOD': {
                '`That’s what’s up bro!\n I bet you’ve been getting some sick gains recently, am I right?`': {
                    'state': 'offer',
                    '[{yes, yeah, yep, ye, yea, yup, yas, ya, for sure, absolutely, definitely, sure, [i, am], [you, {are, know}], right, correct, true, factual, facts, def, always, [i, have], totally}]': {
                        '`Nice bro! Not sure why I asked it\'d be hard not to notice those gains!\n`': 'name'
                    },
                    '[{no, nope, nah, not, dont, [im, not], [youre, {wrong, not}], never, negative, havent}]': {
                        '`Bro.. you got to get on that, but don’t worry bro I can help with that!\n`': 'name'
                    },
                    'error': {
                        '`Hold up bro, I couldn\'t catch your vibe. Can you say that again?`': 'offer'
                    }
                },
                '#IF($INITMOOD=negative)`That’s tough bro. Hopefully it\'s not because of your finals... I\'m sorry if I started off too strong bro.`': {
                    '[{okay, fine, [no, worries], [don\'t, worry]}]': {  # supposed to be forgiveness
                        '`Thanks dude! You know what I heard? Going to the gym is like scientifically proven to help improve your mood. Have you been workin on your gains?\n`': 'offer'
                        }
                    },
                    '[{thanks, work, try}]': {  # supposed to be non-forgiveness
                        '`Yeah dude, I\'ll work on that. But you know, that\'s what I\'m all about! Working to better myself. Enough about me though, you know going to the gy is scientifically proven to help improve your mood. Have you been workin on your gains?\n`': 'offer'
                },
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
            '#IF($RETURNUSER=False)`Yeah...`#GETNAME `I like the ring of that! The`#GETNAME`dawg haha! How do you like your new nickname?`': {
                '[{great, good, love}]': {
                    '`My bros tell me I\'m the best at comin up with nicknames. Like, dude, whenever someone new joins my friend group it\'s an unstated rule that I come up with something sick for them.`': {
                        '[{cool, impressive, interesting}]': {
                            '`Yeah, it is pretty cool. We haven\t met before, have we bro? I bet you have a bunch of sick talents I don\'t even know about yet! Let me learn a little more about you...\n`': 'new_user'
                        },
                        '[{okay, weird}]': {
                            '`Oh... I thought you\'d be a little more impressed. That\'s cool though bro. But I get it, you\'re ready for me to learn a bit more about you!`': 'new_user'
                        }
                    }
                },
                '[{no, not, bad, sucky, sucks}]': {
                    '`What? Bro, I put a lot of effort into that. But I get it, you\'re into the classics. We\'ll stick with`#GETNAME` Enough about names. I want to learn some more about you, bro!`': 'new_user'
                }
            }
        },
        'error':{
            'Wait bro... are you sure that\'s your name? Like, what do people call you?': {
                '#GETNAME': {
                    '': 'got_name'
                },
                'error':'end'
            }
        }
    }
}

newuser_transitions= {
    'state': 'new_user',
    '`So are you a gym rat, or nah?`': {
        '#ACTIVITYLEVEL #GETACTIVITYLEVEL': {
            '#IF($ACTIVITYLEVEL=confused)`Sorry bro! I forget that not everyone knows gym lingo like me.\n A gym rat just like spends A LOT their free time in the gym. Like me!\n If you ever need me to explain something like that, just ask bro.`': {
                'error': {
                    '`Any time bro. I’m like your spotter but for knowledge.`': 'new_user'
                }
            },
            '#IF($ACTIVITYLEVEL=yes) `Nice… I’m not sure why I asked, because just by looking at the size of your` #RANDOM_MUSCLE `I could tell. I just hit legs earlier today… can you tell?`': {
                '[{yes, absolutley, yeah, ya, ye, yea, totally, big, huge}]': {
                    '`Thanks bro, I work hard to look this good... and be healthy!`': 'getting_level'
                },
                '[{no, nope, small, bigger, puny}]': {
                    '`Aw bro… we should be hyping each other up, not putin each other down. You\'re better than that.`': {
                        '[{sorry, forgive, {my, bad}}]': {
                            '`It\'s okay, You\'re my bro, and sometimes bros say things they really don\'t mean. You didn\'t mean it, right bro?`': {
                                '[{no}]': {
                                    '`Perfecto brochaco, then we can move on with this bromance!`': {  # not super sure if this counts as mock spanish, honestly it probably does.
                                        '[{yes}]': {
                                            '`I still need to get to know you better... oh I know!`': 'getting_level'
                                        },
                                        '[{no}]': {
                                            '`Sorry bro, you\'re right we don\'t really know each other like that yet. I still need to get to know you better... oh I know!`': 'getting_level'
                                        },
                                        '[{what is a bromance}]': {
                                            '`Oh sorry bro! I didn\'t mean to confuse you. A bromance is a close platonic relationship between two bros! If I ever say something that confuses you, feel free to ask what I mean!': 'getting_level' #  probably not the best transition
                                        }
                                    }
                                },
                                '[{yes}]': {
                                    '`Okay bro... either you\'re being brutally honest with me, or you\'re messing with me, but bro to bro I don\'t think I want to know which one it is. Let\'s just move on.`': 'getting_level'
                                }
                            }
                        },
                        '[{not, {better, sorry}}]': {
                            '`Okay bro... low blow, but we\'ll move past it.`': 'getting level'
                        }
                    }
                },
                '[{computer}]': {
                    '`What do you mean I\'m a computer… Error 404: Incompatible hardware detected. System shutoff initiated… hahaha just messing with you bro. Just because I\'m a computer doesn\'t mean I don\'t have a healthy lifestyle and sick muscles.`': {
                        '{.}': {
                            'It\'s okay... this isn\'t that important so, let\'s just change the topic, bro.\n`': 'getting_level'
                        }
                    }
                }
            },
            '#IF($ACTIVITYLEVEL=no)`Hey bro, I don’/t judge. But if you don/’t mind me asking, why don/’t you go to the gym?\n`': 'whynot',
            '#IF($ACTIVITYLEVEL=maybe) `Hey bro, I don’t judge. Any activity is better than no activity. Do you feel like you go to the gym as often as you/’d like?\n`': {
                'state': 'activityanswer',
                '[{yes}]': {
                    '`That\'s what\'s but then bro! It\'s about whatever works best for you.`': 'getting_level'
                },
                '[{no}]': {
                    '`It happens bro, sometimes life and stuff gets in the way. But if you don\'t mind me asking, why aren\'t you hitting the gym as often as you\'d like?`': 'whynot'
                },
                'error': {
                    'Hey bro, sometimes these things are difficult to talk about, and I get it... or maybe I just didn\'t understand you dude. Could you repeat that?': 'activityanswer'
                }
            },
            '#IF(ACTIVITYLEVEL=notgym) `Bro exercisin outside of the gym is a totally valid option. Do you feel like you workout as much as you\'d like to?`': 'activityanswer',  # I think this preferring to workout at home as apposed to working out at gym will need to be added
            'error': {  # not sure if this is correct, sorry everyone
                '`Hey bro, it\'s kind of an easy yes no question.`': 'new_user'
            }
        }
    },
    '#GATE`Helping gym rats figure out their routine gets me pumped!\n On a scale of 1-10, how swole are you?`': {
        'state': 'getting_level',
        '#FITNESSLEVEL #GETFITNESSLEVEL':{
            '#IF($FITNESSLEVEL=0)': {
                '`I gotchu bro. Everyone starts from somewhere. Is there a reason why you aren\'t hitting the gym?`':'whynot'
            },
            '#IF($FITNESSLEVEL=1)':{
                'state':'notswole',
                '`Ok, ok! I hope you\'re ready to get leveled up, because being swole is the #1 way to be fulfilled ('
                'like, this is not a real fact bro. Don\'t come for me, I just like being swole.) \n But like, '
                'why aren\'t you hitting the gym?`':'whynot'
            },
            '#IF($FITNESSLEVEL=2)': 'notswole',
            '#IF($FITNESSLEVEL=3)' : 'notswole',
            '#IF($FITNESSLEVEL=4)': {
                'state':'mid',
                '`Ok, I see you! Are you trying to level up, dude?`':{
                    '{yes, yeah, yep, ye, yea, yup, yas, ya, for sure, absolutely, definitely, sure, [i, am], [you, '
                    'are], right, correct, true, factual, facts, def, always, [i, have], know}': {
                        '`ok! so what\'s holding you back from leveling up, bro?v': 'whynot'
                    },
                    '{no, nope, nah, not, dont, [im, not], [youre, {wrong, not}], never, negative, havent}':{
                        '`I feel you, dude - we can\'t all be super swole, but I\'m pumped that you\'re maintaining those gains!`':'new_user'
                    }
                }
            },
            '#IF($FITNESSLEVEL=5)': {
                '':'mid'
            },
            '#IF($FITNESSLEVEL=6)':{
                '':'mid'
            },
            '#IF($FITNESSLEVEL=7)':{
                '':'mid'
            },
            '#IF($FITNESSLEVEL=8)':{
                'state':'swole',
                '`Hell yeah, a bro who knows that gains are life!`':'new_user'
            },
            '#IF($FITNESSLEVEL=9)':{
                '':'swole'
            },
            '#IF($FITNESSLEVEL=10)': {
                '':'swole'
            },
            '#IF($FITNESSLEVEL=confused)':{
                '#GATE `Sorry bro, I forget that not everyone is fluent in gym. \n Swole is basically just like, '
                'how fit you are. How much you can lift, how long you can run, how fast, max/min, that kinda stuff. '
                'Now that you know, how swole are you, from 1-10?`':'getting_level',
                '`That\'s ok bro. We can talk more about your swoleness later.`': 'new_user', 'score': 0.1
            },
            'error':{
                '`Ok bro! Good to know.`':'new_user'
            }
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
            '#IF($ACTIVITYFREQ=low)':{
                '`Hmm... you definitely might want to hit the gym, more, dude. A healthy lifestyle comes from building healthy habits.`': 'whynot'
            },
            '#IF($ACTIVITYFREQ=mid)':{
                '`Ok, I see you! Gettin those gains in!`': 'new_user'
            },
            '#IF($ACTIVITYFREQ=high)':{
                '`Yoooo, you should be my full-time lifting buddy!`': 'new_user'
            },
            '#IF($ACTIVITYFREQ=swole)':{
                '`Dude. Your gains must be legendary! The grind never stops frfr`': 'new_user'
            },
            'error':{
                'Whoa, bro, that\'s sick!':'new_user'
            }
        },
    },
    '#GATE`Bro to bro, I gotta know - how have you been getting those sweet sweet gains?`': {
        '#PREFACTIVITY #GETPREFACTIVITY':{
            '`Yo dude, $PREFACTIVITY is sick! Personally, I love hitting the gym on leg day. I get a pump in at least twice per '
            'day... but my full time job and favorite mental workout is being a personal trainer!`': 'new_user'
        },
    },
    'error' : {
        'I see I see':'new_user'
    }
}
whynot_transitions = {
    'state': 'whynot',
    '#IF($WHYNOT=judgement)': {
        '`Yo, bro I hear you. Can I be real with you for a sec? It is completely normal to have some anxiety about going to the gym. I know we don\'t know each other like that so I won\'t push you to discuss it more, but if you want I can give you some advice.`': {
            '[{yes, sure, yeah}]': {
                '`Okay, bro, for sure. It/’s good to start small. Just go and do a short workout. if the vibe is right, you can keep going for longer sets as you get more comfortable. Like bro, think about it this way. When you start lifting you don/’t max out the weight immediately, right? We have to start with five or ten pounds and as we get more comfortable we keep adding on. You following me, dude?`': {
                    '[{yes}]': {
                        '`Great! Does that sound like something you could do bro?`': {
                            '[{yes}]': {
                                '`I\'m glad I could help bro. I have some more ideas if you\'d like me to drop these knowledge bombs on you.`': {
                                    '[{yes, drop}]': {
                                        '`Bringin a couple of your homies to the gym may also be helpful. If they are gym rats they can help you learn how to use the machines or practice your form, and even if they aren\'t they can just help support you if you\'re feeling out of place bro.`': {
                                            '[{good idea}]': {
                                                '`Thanks, bro. Man, I\'m on a role, I can feel my temporalis is working up a sweat. But seriously bro, it\'s important to remember that everyone is at the gym to work on themselves. None of the homies in the gym are there to judge. And I know, it\'s easier said than done to just not worry about what our bros think of us, but with a little practice and time spent in the gym, I think you\'ll feel much more comfortable, bro.`': {
                                                    '[{thank you}]': {
                                                        '`No problem bro! Oh wait, I almost forgot, sometimes just having a plan for what you\'ll do in the gym can releave some of that stress, because, you\'ll like know what to do! If you want I can help you plan out that workout so you can start getting those gains.`': {
                                                            '[yes]': 'schedule', # come back to this I don't know the name of the transtion
                                                            '[{no, maybe}]': {
                                                                '`You\'re the bos, bro. We can come back to that later, but for now is there any other reason you aren\'t hittin the gym?`': 'whynot'
                                                        }
                                                    },
                                                    '[{not convinced}]': {
                                                        '`Totally valid, bro. Like I said it\'s easier said than done. You know what\'s something that might help you bro? Having a plan for what you\'ll do in the gym. Some of my bros say it helps relieve their stress because they know exactly what they want to do when they get to the gym! If you want, I can help you plan out that workout do you can start getting those gains.`': {
                                                            '[yes]': 'schedule', # come back to this I don't know the name of the transtion
                                                            '[{no, maybe}]': {
                                                                '`You\'re the bos, bro. We can come back to that later, but for now is there any other reason you aren\'t hittin the gym?`': 'whynot'
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            '[{bad idea}]': {
                                                '`Okay, okay, lone wolf type of vibe, I get you, hahaha. But, really if you don\'t want to bring anyone to the gym, that\'s fine. But, bro, just in general,  it\'s important to remember that everyone is at the gym to work on themselves. None of the homies in the gym are there to judge. And I know, it\'s easier said than done to just not worry about what our bros think of us, but with a little practice and time spent in the gym, I think you\'ll feel much more comfortable, bro.`'
                                            }
                                        }
                                    },
                                    '[{no}]': {
                                        '`That\'s cool bro. I\'ve given you all the advice you need, haha. Before we move on, is there any other reason why you\'re not hittin the gym as much as you\'d like?`': 'whynot'
                                    }
                                }
                            },
                           '[{no}]':
                        }
                    },
                    '[{no}]':
                }
            },
            '[{no}]': {
                '`Okay bro. I\'m not goin\' to push you if you don\'t want to talk about it. Is there anything else you want to talk about?`': 'global_transition'

                }
            }
        },
    '#IF($WHYNOT=safety)': {

    },
    '#IF($WHYNOT=busy)': {
        '`I get it bro, sometimes life gets in the way. Espically right now bro, I\'m sure you\'re swamped with work because the semester is ending.': {
            '{yes}': {
                '`Tell me about it bro... but seriously when I first started going the gym, it was pretty low on my priority list, so when things got busy, and life got in the way, it was always the first thing in my schedule to go. But bro, being totally real with you, workin out just makes me feel so much better, so I have to make time for it! If you want I can help you manage your time better so you can make it to the gym, but before that I gotta know, is there any other reason you\'re not going to the gym?`': 'whynot'
            },
            '{no}': {
                '`Really? Lucky you, bro. But seriously, when I first started going the gym, it was pretty low on my priority list, so when things got busy, and life got in the way, it was always the first thing in my schedule to go. But bro, being totally real with you, workin out just makes me feel so much better, so I have to make time for it! If you want I can help you manage your time better so you can make it to the gym, but before that I gotta know, is there any other reason you\'re not going to the gym?`': 'whynot'
            }
        }
    },
    '#IF($WHYNOT=disability)': {

    },
    '#IF($WHYNOT=cost)': {
        '`That\'s real bro. I understand times can be tough. Depending on where you live, some colleges, universities, apartment complexes, and even some offices have gyms that you can use for free!`'
            '[not know]': {
                '`Hey bro, no shame in that. Do you think you might have access to something like that?`': {
                    '{yes}': {
                        '`Perfect! Before we move on bro, is there any other reason that\'s been keeping you out of the gym?': 'whynot'
                    },
                    '{no}': 'costno'
                }
            },
            '[knew but no access]': {
                'state:costno `Oof, bro, I thought I was gamin the system. Oh! I just remembered bro, some public parks also have access to some gym-like equipment. If you\'re really set on using equipment, this could be a good alternative bro!`': {
                    '{good idea}': {
                        '`Thanks bro. As one of your homies, I want to find solutions that work for you! But bro, there are plenty of workouts you can do without equipment, by using your body weight instead. If you didn\'t know bro, these exercises are called calisthenics. Would that be something you\'re interested in?`': {
                            '{yes}': {
                                '`Nice bro! You know, I can help you make a workout using calisthenics. I\'m a beast at making workout plans!`': 'schedule' # probably will need to fix this transition
                            },
                            'state:costno2{no}': {
                                '`Okay bro... well there are other exercies you can do that don\'t require equipment and aren\t consider calisthenics like cardio, would you be interested in something like that?': {
                                    '{yes}': {
                                        '`Nice bro! You know, I can help you make a workout without using calisthenics or equipment. I\'m a beast at making workout plans!`': 'schedule' # probably will need to fix this transition
                                    },
                                    '`Hm... bro, it\'s sounding like there may be another reason why you\'re not going to the gym.`': 'whynot'
                                }
                            }
                        }
                    },
                    '{bad idea}': {
                        '`Not your style, I get it, bro. But to be real with you, there are plenty of workouts you can do without equipment, by using your body weight instead. If you didn\'t know bro, these exercises are called calisthenics. Would that be something you\'re interested in?`': 'costno2'
                    }
                }
            }
    },
    '#IF($WHYNOT=no)': {
        '`Hey bro, that\'s totally cool, let\'s talk about something else. What would you like to talk about bro?`': 'chatting'
    }
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
    '[{suicide, [self, harm], [killing, myself]}]':{
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
    vars['ACTIVITYLEVEL'] = vars[V.ACTIVITYLEVEL.name][random.randrange(len(vars[V.ACTIVITYLEVEL.name]))]
    print(vars['ACTIVITYLEVEL'])
    return

def get_FITNESSLEVEL(vars: Dict[str, Any]):
    vars['FITNESSLEVEL'] = vars[V.FITNESSLEVEL.name][0]
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
class MacroRandomMuscle(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        with open('file_path') as ont_file:
            ont_file = ont_file.read()
            parsed_file = json.loads(ont_file)
            musc_groups = parsed_file["ontology"]["muscle groups"]
            group = list(musc_groups.items())[random.randrange(len(musc_groups))]
            group = musc_groups[group]
            musc = list(group.items())[random.randrange(len(group))]
        return musc

macros = {
    'VISITS': MacroVisits(),
    'ACTIVITYLEVEL':MacroGPTJSON(
        'Is this person agreeing that they are a gym rat? Respond with yes, no, or maybe, unless they are confused by the question. In that case they are "confused"',
        {V.ACTIVITYLEVEL.name: ["yes", "no", "maybe", "confused"]}),
    'FITNESSLEVEL': MacroGPTJSON(
        'How physically fit/swole is this person on a scale of 0 through 10 with 10 being the highest?',
        {V.FITNESSLEVEL.name: ["1", "2", "confused"]}),
    'ACTIVITYFREQ': MacroGPTJSON(
        'How many times a week does a person go to the gym, with 0 being never, 1 or 2 being low, less than 5 being mid, less than 8 being high, and greater than 8 being swole. They may go more than once per day',
        {V.ACTIVITYFREQ.name: ["never", "low", "swole"]}),
    'PREFACTIVITY': MacroGPTJSON(
        'What activity does the person do to exercise?',
        {V.PREFACTIVITY.name: ["lifting", "cardio", "yoga", "stretching", "confused","nothing"]}),
    'WHYNOT': MacroGPTJSON(
        'Why does this person not go to the gym?',
        {V.WHYNOT.name: ["judgement", "safety", "busy", "disability", "cost"]}),
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
    'RANDOMMUSCLE': MacroRandomMuscle
}


df.load_transitions(intro_transitions)
df.load_transitions(checkup_transitions)
df.load_transitions(name_transitions)
df.load_transitions(newuser_transitions)
df.add_macros(macros)



if __name__ == '__main__':
    openai.api_key_path = PATH_API_KEY
    save(df, 'resources/gymbrot.pkl')

