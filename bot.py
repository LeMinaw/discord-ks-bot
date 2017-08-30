from discord import Client
from urllib.request import urlopen
import re


KS_URL = "https://www.kickstarter.com/projects/skywanderers/skywanderers"


class Progress():
    """Kickstarter progress object."""
    def __init__(self, url):
        """Inits a Progress object from a kickstarter page URL."""
        page = urlopen(url).read().decode()
        reg_goal    = re.compile(r'data-goal="([0-9]+).[0-9]+"', re.M)
        reg_pledged = re.compile(r'data-pledged="([0-9]+).[0-9]+"', re.M)
        reg_backers = re.compile(r'data-backers-count="([0-9]+)"', re.M)
        reg_duration = re.compile(r'data-duration="([0-9]+)"', re.M)
        reg_remaining = re.compile(r'data-hours-remaining="([0-9]+)"', re.M)

        self.goal = int(reg_goal.search(page).group(1))
        self.pledged = int(reg_pledged.search(page).group(1))
        self.backers = int(reg_backers.search(page).group(1))
        self.duration = int(reg_duration.search(page).group(1)) * 24 # Duration is provided in days
        self.remaining = int(reg_remaining.search(page).group(1))

    @property
    def percent(self):
        """Returns the percentage of funding acomplished at this time."""
        return int(self.pledged / self.goal * 100)

    @property
    def per_back(self):
        return self.pledged / self.backers

    @property
    def per_hour(self):
        return self.pledged / (self.duration - self.remaining)

    @property
    def eta(self):
        return self.per_hour * self.duration

    def bar(self, size=20):
        """Computes a progress bar of arbitrary size."""
        bar = ''
        full_chars_nb = int(self.percent / 100 * size)
        if size % 2 != 0:
            size += 1
        for i in range(size):
            if i == size / 2:
                bar += str(self.percent) + '%'
            if i < full_chars_nb:
                bar += '='
            else:
                bar += '-'
        return "Kickstarter progress: [%s] (%s/%s)" % (bar, self.pledged, self.goal)

    def fullinfo(self):
        return "Kickstarter full info:\n    Progress: %s%% done, %s%% to go.\n    Funds: %s pledged, goal %s.\n    Backers: %s, per-back avg %.2f.\n    Time: %s elapsed hours, %s hours remaining.\n    Per-hour avg: %.2f.\n    Estimated end funds: %d." % (self.percent, 100-self.percent, self.pledged, self.goal, self.backers, self.per_back, self.duration-self.remaining, self.remaining, self.per_hour, self.eta)


client = Client()

@client.event
async def on_message(message):
    if message.content.startswith('!ks'):
        progress = Progress(KS_URL)
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

client.run('MzUyMzU0NTc2MjI3MTA2ODE2.DIf7fQ.EvhOV3JoZkx6FSOJF3I28r3RtUw')
