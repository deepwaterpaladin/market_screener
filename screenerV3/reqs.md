# V3 Screener

## V1 Screener Additions

- FV Upside metric
    - Calculation methodology: 7X aFCF figure + net-cash (this is net-debt inverted) [compared to the current market cap, as a percentage].
    - explanation: This figure should then be compared to the current market cap. The distance between the two numbers should then be displayed as a percentage. 
    - EX: Market cap = £100 and Upside figure = £200. The percentage distance from £100 to £200 is +100% and so this is what is displayed on the sheet in the ‘upside’ box for that stock. 
- 5-Y Price metric
    - Calculation methodology: ([5-Y high - current stock price] / current stock price) * 100 
    - explanation: The distance between today's stock price and the highest share price from the past 5 years, as a percentage. I want to see what percentage the stock can rise before reaching its 5-Y high. If today's price is the highest from the past 5 years then it should simply display 'N/A'

## V1 Screener Alterations

- EV/aFCF earnings Ratio
- Update data type to percentage rather than ratio;
- change default behaviour for "N/A" to display "100%"
- if the EV is negative the yield will display as a default '100%'.
- Column Updates
    - New structure: | Ticker | Name | NCAV Ratio | EV Yield | TBV Ratio | FCF Yield | FV Upside | 5-Y Price | Country
- Implement Custom Ranking Algorithm
  - Sort by: NCAV ratio (lowest at the top); if no NCAV ratio then it should be ranked by TBV ratio (lowest at the top instead); if no TBV ratio either, then it should be ranked by upside percentage with the highest percentage at the top.

## V2 Screener Additions

- FV Upside metric 
    - Calculation methodology: 7X aFCF figure + net-cash (this is net-debt inverted) [compared to the current market cap, as a percentage]. 
    - explanation: This figure should then be compared to the current market cap. The distance between the two numbers should then be displayed as a percentage. 
    - EX: Market cap = £100 and Upside figure = £200. The percentage distance from £100 to £200 is +100% and so this is what is displayed on the sheet in the ‘upside’ box for that stock.
- 5-Y Price metric 
    - Calculation methodology: ([5-Y high - current stock price] / current stock price) * 100 
    - explanation: The distance between today's stock price and the highest share price from the past 5 years, as a percentage. I want to see what percentage the stock can rise before reaching its 5-Y high. If today's price is the highest from the past 5 years then it should simply display 'N/A'

## V2 Screener Alterations

- EV/aFCF earnings Ratio
  - Update data type to percentage rather than ratio
  - change default behaviour for "N/A" to display "100%"
  - if the EV is negative the yield will display as a default '100%'.
- V2 screener displays each column rather than displaying 'N/A' if it doesn't fall into the correct criteria. it will display the ratio (even if its above 2) and only display 'N/A' if the NCAV is actually negative.
- Column Updates - New structure: | Ticker | Name | NCAV Ratio | EV Yield | TBV Ratio | FCF Yield | FV Upside | 5-Y Price | Country 
- Implement Custom Ranking Algorithm 
    - Sort by: NCAV ratio (lowest at the top); if no NCAV ratio then it should be ranked by TBV ratio (lowest at the top instead); if no TBV ratio either, then it should be ranked by upside percentage with the highest percentage at the top.

## Cloud Development

- Build pipeline