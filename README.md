# SPX_Futures_Roll_Strategy
If we want to gain a continuous exposure to an illiquid asset, investing in a future and cash portfolio is the best strategy. The Project aims to design the optimal monthly roll strategy for SPX futures such that we have minimum roll cost. I predict the roll cost that can occur over a 1yr rolling basis to find if the futures are costlier than holding a stock. 

## Introduction: 
To get exposure to any asset, we can either buy the asset or buy the futures traded on the asset. The benefits are : 
1) Buying the futures provides liquidity to the portfolio. 
2) The price of a futures contract is just a fraction of the stock price so we always have extra cash which can be invested in a risk free asset. 
3) Also if the stock/index is illiquid, holding the original index is risky. Having exposure to a future gives us the flexibility to exit out of the contract easily. 

But using futures comes with its caveats. Futures expire every quarter and we need to roll them to the next month future in order to maintain exposure. This creates a frictional cost or futures roll cost which needs to be considered before choosing futues over stock.

## Objective: 
In this project we take the S&P 500 index and try to find the optimal roll strategy for a futures + cash portfolio, such that the roll cost is minimised. 
I use linear programming to find the optimal weights to be rolled on each day (for 5 days) to get the lowest cost possible. 
The idea and code is replicable to any asset, to compare the friction cost of investing in a future vs asset.

## 
