# IMC Proesperity 2

My best guess at figuring this out on my own with no prior knowledge.
I finished 573rd out of approximately 10,000 participants.

## Useful Links

- [Wiki - Notion](https://imc-prosperity.notion.site/Prosperity-2-Wiki-fe650c0292ae4cdb94714a3f5aa74c85).
- [Backtester API - GitHub](https://github.com/jmerle/imc-prosperity-2-backtester). (No support for round 2!)
- [Visualizer - GitHub Pages](https://jmerle.github.io/imc-prosperity-2-visualizer/?/visualizer).
- [Stanford-Cardinal - Github](https://github.com/ShubhamAnandJain/IMC-Prosperity-2023-Stanford-Cardinal). This team finished 2nd in 2023. I based my round 1 on their algorithms.
- [Leaderboard - Github Pages](https://jmerle.github.io/imc-prosperity-2-leaderboard/)

## Notes

1. The wiki describes the commodities introduced in each round.
2. "Writing an Algorithm in Python" on the wiki is a must read. It explains how to interact with the platform.
3. I can't remember where the logger class came from, but it is required to interact with the visualizer.
4. Keep `datamodel.py` locally for linting.
5. The backtester will only evaluate the new commodities introduced in that round. So Starfruit and Amethysts cannot be tested when in round 3 of the backtester.