![Alt-Tag](https://i.imgur.com/V5ERvU4.png)
### About:
NERYS will monitor specified sites for keywords and sends a Discord alert when a page has a specified keyword. This can be used to monitor any site on a product release date to automatically detect when a product has been uploaded. Useful when monitoring hundreds of sites for shops in different timezones.

### Usage:
Add your Discord webhook URL in the appropriate fields (line 143 on other-sites.py and line 204 on shopify-sites.py), surrounded by quotation marks. You can set keywords you want to monitor at the bottom of each of the scripts, following the same format as the example. Seperate keywords with a '-' instead of a ' ' on other-sites.py. Add sites to monitor to each of the respective text files, following the same format as the examples (I suggest using Notepad++, Notepad does something weird). Proxies should also be one per line, following the same format as the examples provided in <proxies.txt>.

### Complete:
- find all products on Shopify site by keyword
- send discord notifications
- monitor for new products
- optimization for Shopify to return product checkout links by size
- find all products on other sites by keyword
- attempt to get product page links for universal sites

### Planned Updates:
- monitor for Shopify restocks
- monitor for restocks on other sites
-- find sold out by keyword
-- find sizes by keyword
-- find countdown timer by keyword
- detect cloudflare
- get product picture for other sites
- optimization for footsites

Have suggestions on how to make the monitor better? Let me know via Twitter (@snivynGOD)!

### Credits:
Niveen Jegatheeswaran - That's Me! - https://github.com/snivyn/, https://twitter.com/snivynGOD

kyb3r - Discord Embed - https://github.com/kyb3r/
