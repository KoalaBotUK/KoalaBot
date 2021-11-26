# Contributing to KoalaBot

Thank you for taking time to contribute, any change at all continues to make Koala better!\
If you are here just to ask a question head over to our support [Discord server](https://discord.koalabot.uk) where our developers can help you out!

## 1. Feature Request/ Bug Report

What is it that you want to be added or changed?
Please create an issue on the KoalaBot GitHub page using the provided issue templates, giving **detailed** information about your request.

Create an issue [here](https://github.com/KoalaBotUK/KoalaBot/issues/new/choose).

## 2. Getting Started with Implementation

### Fork the Repo (Public Contributor)

Fork the [KoalaBot GitHub repository](https://github.com/KoalaBotUK/KoalaBot), it is fine to leave the name as KoalaBot.

You will then need to clone the repo you've created locally to make your edits. Before you begin your changes, make sure you can both run the bot and the tests, instructions for which are [here](https://github.com/KoalaBotUK/KoalaBot/blob/master/README.md).

### Make a Branch (KoalaBot Dev Team)

Make a branch with a descriptive name with lowercase words separated with `-` (e.g. `react-for-role` or `fix-verify-email-formatting`).

You will then need to clone the repo you've created locally to make your edits. Before you begin your changes, make sure you can both run the bot and the tests, instructions for which are [here](https://github.com/KoalaBotUK/KoalaBot/blob/master/README.md).

## 3. Make your changes

While you make edits, use frequent commits to describe progression, do **not** commit once when complete or when massive changes have been made as this makes it hard to debug.

Things to ensure you do during implementation:

- Follow [PEP-8](https://www.python.org/dev/peps/pep-0008/) for naming and formatting
- Include documentation of each method and class within your code through RestructuredText docstrings
- If any new bot commands are added, modify `documentation.json`
- Add tests for any created methods using [pytest](https://docs.pytest.org/) and [dpytest](https://dpytest.readthedocs.io/) (or explain in the pull request why a test is missing)
- Look out for and fix common security issues (e.g. sql injection)

## 4. Create a Draft Pull Request (optional)

If you are ever confused while developing, refer to other examples or message us on our Support Discord.
However, if your question is specific to parts of your code it is a good idea to instead make a pull request (below) and mark as draft. This allows us to answer questions during development and reference your code.

All KoalaBot Dev Team members must create draft pull requests for their branch. This allows your project lead to monitor progress and offer help when needed.

## 5. Create a Pull Request

Once you are ready for a review you will need a pull request for your fork/branch.

Please follow the instructions in the pull request template provided and check off the applicable checkboxes. A clear summary of your changes with the issue link (using `close #n` where `n` is the issue number) allows quick reviews to be done.

## 6. Review and Merge

Our senior developers will review all completed open pull requests that have completed all the required checks. Once they have reviewed you may have to make changes if requested, or they will accept your change and merge it to master.

You have now contributed to a great cause, well done!

### Joining the Development Team

If after this experience you feel like you would like to help further with KoalaBot please contact `@JayDwee#4233` on Discord about joining the KoalaBot Development Team.
