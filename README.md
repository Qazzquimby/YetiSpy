# Eternal Card Evaluator
Helps [Eternal][https://www.direwolfdigital.com/eternal/] players evaluate cards based on their 
frequency of use in decks the user is interested in.

Eternal Card Evaluator takes the user's card collection and a weighted list of 
[EternalWarcry][https://eternalwarcry.com/] deck searches, and exports an ordered list of cards 
with the number of relevant decks that have at least one more copy of the card than the user has 
in their collection. Focusing on buying the cards higher on the list will bring the user closest 
to building the relevant decks.

## Setup
If you're reading this from the Github page, click "Clone or download," "Download ZIP," and 
extract the archive.

Navigate to the dist folder inside. *All interaction with Eternal Card Evaluator must take place 
in the dist folder.* Everything outside of the dist folder can be safely deleted, 
and is only there to allow viewing and modification of the source code.

##### Supply your collection
1. In Eternal -> Cards -> My Collection -> press "Export Collection."
2. Paste to collection.txt (the one in dist) to supply your collection data.

##### Choose the decks you're interested in

Eternal Card Evaluator reads decks from [EternalWarcy Deck Searches][https://eternalwarcry.com/decks].

Use the search criteria to make a search for decks that you want to emulate or build.

This is subjective, but some things you may want to look at are:
- Recent tournament decks.
- Decks including cards you want to play around.
- Decks by notable players.

Note that any very large searches, such as "all time" searches, may take a very long time to 
process, save as a very large file, and even cause out-of-memory crashes. I recommend using 90 
days as a maximum.

In the future, additional search parameters may be added, such as filtering by views or rating.

##### Supply the decks you're interested in
1. Supply any search criteria you want in the 
[EternalWarcy Deck Search][https://eternalwarcry.com/decks] interface.
2. Press search. Stay on the first page of the search results (URL cannot have a "p=x" term).
3. Open search_urls.csv
4. Add a line to the file of the form:"Search Name, Weight, Search URL"
5. Repeat from 1. any number of times, to add additional searches.

Search Name is used to label the output for that search.
Weight is the proportion that cards from that search will be prioritized. A card used in a search 
with a weight of 4 will count for twice as much as a card in a search with a weight of 2.

For example `Tournament 15, 2.5, https://eternalwarcry.com/decks?td=1&mdb=15` represents all 
tournament decks in the last 15 days.

##### Getting your results
Whenever a new set comes out, run "Update_Cards.exe." If this program hasn't been updated in a 
while, it may be necessary to run the first time you use it. Update_Cards.exe learns from 
EternalWarcry, so you may have to wait for them to update with the new set.

Whenever you change your deck searches, or want to load in recent changes to the searches, run 
"Update_Decks.exe." This grabs any new decks in the search, and deletes decks that no longer fit 
the search. It tries not to redo any work, so it shouldn't take long if it only has to make a 
small change.

To update your results, run "Generate_Overall_Value.exe." This combines the statistics from the 
decks, your collection, and the weights you provided for the deck searches, to output a file 
called "**Dist/Output/Overall_Value.json**." This is the only file you probably care about. Most 
other files in output are for intermediate steps, and are less readable.

##### Interpreting your results.
Overall_Value.json contains a series of blocks representing cards, where cards at the top used 
more often in your deck searches.

"New_Count" is the number of that card you will own after buying one more.

"Value" is approximately the percentage of decks in your searches that have at least "New_Count" 
copies of that card. That percentage is calculated for each of your deck searches, and then 
averaged together based on the weights you gave. If a card was used in every deck in a search 
with priority 10, and never used in a seaerch with priority 1, the value would be 90. 
 
 Here is some example data for a user with an empty collection, looking to build tournament decks:
```
[
    {
        "card_name": "Torch",
        "new_count": 1,
        "rarity": "common",
        "value": 47.55012814714307
    },
    {
        "card_name": "Vanquish",
        "new_count": 1,
        "rarity": "uncommon",
        "value": 34.19267299864315
    },
    {
        "card_name": "Seek Power",
        "new_count": 1,
        "rarity": "common",
        "value": 34.132368460726674
    }, ...
```

## The Future
In no particular order, I hope to add:
- (High Priority) Evaluation of how to spend gold, to maximize finding high priority cards.
- Automatically handling of updates, rather than making the user click multiple exes.
- Additional search parameters, such as by rating or views.

All of these are somewhat difficult, and may not happen.

## Bugs
I hope not.

Please first make sure instructions were followed:
 - Only use contents of dist folder.
 - Correctly format search_urls.csv
 - Make sure cards and decks have been updated before clicking generate_overall_value.exe
 
 Send me the crash dialogue.
 If the window is immediately closing, make a bat file with the contents
 ```
 start <exe that's not working>
 pause
 ```
and run that. That should store the output.

If there is no output, be careful that you aren't missing search_urls, decks or cards. 

[https://www.direwolfdigital.com/eternal/]: https://www.direwolfdigital.com/eternal/
[https://eternalwarcry.com/]: https://eternalwarcry.com/
[https://eternalwarcry.com/decks]: https://eternalwarcry.com/decks
