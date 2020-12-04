import pytest
from cogs import Voting


class Fake:
    def __getattr__(self, item):
        setattr(self, item, Fake())
        return getattr(self, item)


ctx = Fake()
ctx.author.id = 1234
ctx.guild.id = 4567
cog = None


def test_two_way():
    def test_asserts(f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except AssertionError:
            return
        raise AssertionError

    # test internal asserts don't false positive
    t = Voting.TwoWay({1: 2, 3: 4})
    t2 = Voting.TwoWay({1: 2, 2: 1, 4: 3})
    assert t == t2

    # test an invalid dict cannot be made
    test_asserts(Voting.TwoWay, {1: 2, 2: 3})

    def ta2():
        t = Voting.TwoWay()
        t[1] = 2
        t[2] = 3
        test_asserts(ta2)


def test_vote_manager_general():
    vm = Voting.VoteManager()
    assert not vm.active_votes
    vote = vm.create_vote(ctx, "Test Vote")
    assert ctx.author.id in vm.active_votes.keys()
    assert vm.get_vote(ctx) == vote
    assert vm.has_active_vote(1234)
    vm.cancel_vote(1234)
    assert not vm.has_active_vote(1234)


def test_vote_general():
    vm = Voting.VoteManager()
    vote = vm.create_vote(ctx, "Test Vote")
    assert vote.id == ctx.author.id and vote.guild == ctx.guild.id and vote.title == "Test Vote"
    assert not vote.is_ready()

    vote.add_role(7890)
    assert 7890 in vote.target_roles
    vote.remove_role(7890)
    assert 7890 not in vote.target_roles

    vote.set_vc(1234)
    assert vote.target_voice_channel == 1234

    opt1 = Voting.Option("test option 1", "test body 1")
    opt2 = Voting.Option("test option 2", "test body 2")
    vote.add_option(opt1)
    vote.add_option(opt2)
    assert len(vote.options) == 2
    assert vote.is_ready()

    vote.remove_option(1)
    assert vote.options[0] == opt2
