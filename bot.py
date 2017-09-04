from discord import Client, Object
from urllib.request import urlopen
import asyncio
from os import getenv
import re


KS_URL = "https://www.kickstarter.com/projects/skywanderers/skywanderers" # Url to the Kickstarter page
KS_GOALS = [50000] # Kickstarter goal detected automatically. This is only for supplementary goals.
DISCORD_CHANNELS = [241014195884130315, 271382095383887872]
DEBUG = True

class Progress():
    def __init__(self, url, goals=[]):
        self.kwargs = {'url':url, 'goals':goals}

        page = urlopen(url).read().decode()
        reg_title     = re.compile(r'"og:title" content="([-\w\s]+)"', re.M)
        reg_currency  = re.compile(r'"money (\w+) project_currency_code"', re.M)
        reg_goal      = re.compile(r'data-goal="([0-9]+).[0-9]+"', re.M)
        reg_pledged   = re.compile(r'data-pledged="([0-9]+).[0-9]+"', re.M)
        reg_backers   = re.compile(r'data-backers-count="([0-9]+)"', re.M)
        reg_duration  = re.compile(r'data-duration="([0-9]+)"', re.M)
        reg_remaining = re.compile(r'data-hours-remaining="([0-9]+)"', re.M)

        self.title    = reg_title.search(page).group(1)
        self.currency = reg_currency.search(page).group(1).upper()
        self.goals = [int(reg_goal.search(page).group(1))] + goals
        self.goals.sort()
        self.pledged   = int(reg_pledged.search(page).group(1))
        self.backers   = int(reg_backers.search(page).group(1))
        self.duration  = int(reg_duration.search(page).group(1)) * 24 # Duration is provided in days
        self.remaining = int(reg_remaining.search(page).group(1))

        self.comissions = {
            'total_percent': 5.0,
            'per_back_percent': 3.0,
            'per_back_fixed': 0.20
        }

        if self.currency == 'HKD' or self.currency == 'SGD':
            self.comissions['per_back_percent'] = 4.0

        elif self.currency == 'MXD':
            self.comissions['per_back_percent'] = 4.0
            self.comissions['per_back_fixed'] = 0.60

        elif self.currency == 'NOK' or self.currency == 'SEK':
            self.comissions['per_back_fixed'] = 0.30

    @property
    def goal(self):
        for goal in self.goals:
            if goal > self.pledged:
                return goal
        return max(self.goals)

    @property
    def goal_nb(self):
        for i, goal in enumerate(self.goals):
            if goal == self.goal:
                return i + 1
        return len(self.goals)

    @property
    def goals_cleared(self):
        return [goal for goal in self.goals if self.pledged > goal]

    @property
    def goals_uncleared(self):
        return [goal for goal in self.goals if self.pledged < goal]

    @property
    def goals_cleared_nb(self):
        return len(self.goals_cleared)

    @property
    def goals_uncleared_nb(self):
        return len(self.goals_uncleared)

    @property
    def percent(self):
        return int(self.pledged / self.goal * 100)

    @property
    def percent_remaining(self):
        return 100 - self.percent

    @property
    def elapsed(self):
        return self.duration - self.remaining

    @property
    def per_back(self):
        return self.pledged / self.backers

    @property
    def per_hour(self):
        return self.pledged / self.elapsed

    @property
    def comission(self):
        return self.pledged * (self.comissions['total_percent']/100 + self.comissions['per_back_percent']/100) + self.backers * self.comissions['per_back_fixed']

    @property
    def comission_percent(self):
        return self.comission / self.pledged * 100

    @property
    def eta(self):
        return self.per_hour * self.duration

    def refresh(self):
        self.__init__(**self.kwargs)

    def display_bar(self, size=20):
        bar = ''
        full_chars_nb = int(self.percent / 100 * size)
        if size % 2 != 0:
            size += 1
        for i in range(size):
            if i == size / 2:
                bar += '%s%%' % self.percent
            if i < full_chars_nb:
                bar += '='
            else:
                bar += '-'
        return "{s.title} progress: [{bar}] ({s.pledged}/{s.goal}, goal #{s.goal_nb})".format(bar=bar, s=self)

    def display_info(self):
        return "{s.title} information:\n    Progress: {s.percent}% done, {s.percent_remaining}% to go, goal #{s.goal_nb}.\n    Funds: {s.pledged} pledged, current goal {s.goal}.\n    Goals: {s.goals_cleared_nb} cleared, {s.goals_uncleared_nb} remaining.\n    Backers: {s.backers}, per-back avg {s.per_back:.2f}.\n    Time: {s.elapsed} elapsed hours, {s.remaining} hours remaining.\n    Per-hour avg: {s.per_hour:.2f}.\n    Estimated end funds: {s.eta:.0f}.\n    Kickstarter comission: {s.comission:.0f} ({s.comission_percent:.2f}%)\n    Currency: {s.currency}".format(s=self)

    def display_goals(self):
        msg = ''
        for goal in self.goals_cleared:
            msg += "\n    %s [CLEARED!]" % goal
        for goal in self.goals_uncleared:
            if goal == self.goal:
                msg += "\n    %s [PROGRESS (%s%%)]" % (goal, self.percent)
                continue
            msg += "\n    %s" % goal
        return "%s goals:%s" % (self.title, msg)


async def check_ks(progress, chans_ids, delay=60):
    await client.wait_until_ready()

    progress.refresh()
    oldProgress = progress.percent

    while not client.is_closed:
        progress.refresh()
        if progress.percent > oldProgress:
            for chan_id in chans_ids:
                channel = Object(id=chan_id)
                msg = "One percent closer !\n`%s`" % progress.display_bar(40)
                await client.send_message(channel, msg)
            oldProgress = progress.percent
        await asyncio.sleep(delay) # task runs every 60 seconds


client = Client()
progress = Progress(KS_URL, KS_GOALS)

@client.event
async def on_message(message):
    if message.content.startswith('!ks'):
        progress.refresh()
        if message.content == '!ks':
            msg = "`%s`" % progress.display_bar(40)
        else:
            if message.content.startswith('!ks more'):
                msg = "`!ks more` is obsolete. Please use `!ks info` or `!ks all`."
            elif message.content.startswith('!ks goals'):
                msg = "```%s```" % progress.display_goals()
            elif message.content.startswith('!ks info'):
                msg = "```%s```" % progress.display_info()
            elif message.content.startswith('!ks all'):
                msg = "```%s\n\n%s\n\n%s```" % (progress.display_bar(20), progress.display_goals(), progress.display_info())
            elif message.content.startswith('!ks help'):
                msg = "```Kickstarter commands:\n    !ks\n    !ks goals\n    !ks info\n    !ks all\n    !ks help```"
            else:
                msg = "Unknown command `%s`. Please see `!ks help`." % message.content
        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.loop.create_task(check_ks(progress, DISCORD_CHANNELS, 60))

if DEBUG:
    print(progress.display_bar(60))
    print(progress.display_goals())
    print(progress.display_info())
else:
    client.run(getenv('DISCORD_TOKEN'))
