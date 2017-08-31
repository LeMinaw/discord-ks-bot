from discord import Client
from urllib.request import urlopen
import re


KS_URL = "https://www.kickstarter.com/projects/skywanderers/skywanderers" # Url to the Kickstarter page
KS_GOALS = [50000] # Kickstarter goal detected automatically. This is only for supplementary goals.
DEBUG = False

class Progress():
    """Kickstarter progress object."""
    def __init__(self, url, goals=[]):
        """Inits a Progress object from a kickstarter page URL."""
        page = urlopen(url).read().decode()
        reg_goal    = re.compile(r'data-goal="([0-9]+).[0-9]+"', re.M)
        reg_pledged = re.compile(r'data-pledged="([0-9]+).[0-9]+"', re.M)
        reg_backers = re.compile(r'data-backers-count="([0-9]+)"', re.M)
        reg_duration = re.compile(r'data-duration="([0-9]+)"', re.M)
        reg_remaining = re.compile(r'data-hours-remaining="([0-9]+)"', re.M)

        goals.append(int(reg_goal.search(page).group(1)))
        self.goals = sorted(goals)
        self.pledged = int(reg_pledged.search(page).group(1))
        self.backers = int(reg_backers.search(page).group(1))
        self.duration = int(reg_duration.search(page).group(1)) * 24 # Duration is provided in days
        self.remaining = int(reg_remaining.search(page).group(1))

    @property
    def goal(self):
        """Returns the next goal to achieve."""
        for goal in self.goals:
            if goal > self.pledged:
                return goal
        return max(self.goals)

    @property
    def goal_nb(self):
        """Returns the current goal number."""
        for i, goal in enumerate(self.goals):
            if goal == self.goal:
                return i + 1
        return len(self.goals)

    @property
    def goals_cleared(self):
        """Returns the list of all cleared goals."""
        return [goal for goal in self.goals if self.pledged > goal]

    @property
    def percent(self):
        """Returns the percentage of funding acomplished at this time."""
        return int(self.pledged / self.goal * 100)

    @property
    def per_back(self):
        """Returns the average funds gained per back."""
        return self.pledged / self.backers

    @property
    def per_hour(self):
        """Returns the average funds gained per hour."""
        return self.pledged / (self.duration - self.remaining)

    @property
    def eta(self):
        """Gives an innacurate estimate of the funds at the end."""
        return self.per_hour * self.duration

    def bar(self, size=20):
        """Computes a progress bar of arbitrary size."""
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
        return "Kickstarter progress: [%s] (%s/%s, goal #%s)" % (bar, self.pledged, self.goal, self.goal_nb)

    def fullinfo(self):
        """Returns full Kickstarter information."""
        return "Kickstarter full info:\n    Progress: %s%% done, %s%% to go, goal #%s.\n    Funds: %s pledged, current goal %s.\n    Goals: %s cleared, %s remaining.\n    Backers: %s, per-back avg %.2f.\n    Time: %s elapsed hours, %s hours remaining.\n    Per-hour avg: %.2f.\n    Estimated end funds: %d." % (self.percent, 100-self.percent, self.goal_nb, self.pledged, self.goal, len(self.goals_cleared), len(self.goals)-len(self.goals_cleared), self.backers, self.per_back, self.duration-self.remaining, self.remaining, self.per_hour, self.eta)


client = Client()

@client.event
async def on_message(message):
    if message.content.startswith('!ks'):
        progress = Progress(KS_URL, KS_GOALS)
        if message.content.startswith('!ks more'):
            msg = "```%s\n\n%s```" % (progress.bar(20), progress.fullinfo())
        else:
            msg = "`%s`" % progress.bar(40)
        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


if DEBUG:
    progress = Progress(KS_URL, KS_GOALS)
    print(progress.bar(60))
    print(progress.fullinfo())
else:
    client.run('MzUyMzU0NTc2MjI3MTA2ODE2.DIf7fQ.EvhOV3JoZkx6FSOJF3I28r3RtUw')
