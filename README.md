# TopNews-CW 💫

This is a project on analyzing international news with automatic translation and clustering. Developed for [Common World](https://common.world).

### History 

This project was started when I was in my first year at ITMO University. Then, I knew almost nothing on how to build good software and was just doing things in the way that they worked, somehow. No testing, no refactoring 😔 Thus, there is a lot of legacy code that looks awful. 

### Status

I am still developing the system. When adding new functionality, I try to write the best code I can and test it all. My attitude to programming has changed dramatically, which is good but brings me pain when I look at the legacy code I've created over 3 years that passed. However, with time I will try to refactor, optimize and cover with tests all of this code. 

I have created this table to display the current status of different modules of the system.

| Module         | Labels       | Comments                  |
|----------------|--------------|---------------------------|
|app |**not_tested** *legacy*|May need to delete|
|corpus |**tested_manually** *legacy* |Needs refactoring
|db_management | ✅
|document |**not_tested** *legacy* |Needs refactoring
|draw_graph|**not_tested** *legacy*|Requires consideration
|find_connection|**not_tested** *legacy*|Requires consideration
|get_news|**not_tested** *legacy*|May need to delete|
|main|✅
|newsapi|✅
|utils|**not_tested** *legacy*|Need to split into different modules
|wide|**not_tested** *legacy*|Need to split into different modules
|xl_stats|**tested_manually**|
|text_processing|**not_tested** *legacy*|Needs refactoring
|scrapnews|**not_tested** *legacy*|May need to delete|
