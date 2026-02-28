# Lecturer Notes (Dr. Oren Glickman)

**These are the advisor's notes on the project overview. We need to follow these guidelines throughout the project.**

---

Hi Adir.
The project's overview looks good.
It would be really exciting to get this done and see the results.
As for the ballot/municipality representation - "Each municipality will be represented as a vector of vote shares for different political parties or political blocs", we can play around with various options: Raw party votes (in percents), Manual grouping (as you suggested) or algorithmically lowering the dimension of number of parties to a smaller set (using some sort of unsupervised method)
Another thing is  to play with is the distance metric used to compare two such vectors (Euclidian distance, Jensen–Shannon, ...).

In terms of code you can easily plus and play the representation and distance metric to work with any clustering algorithm you use.

In terms of existing related work, here is one I found that may be relevant - https://arxiv.org/pdf/1703.02867.

Keep me updated with you progress.

Oren.
