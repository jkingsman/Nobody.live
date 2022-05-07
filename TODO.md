* Add ORM to mop up ugly stream query logic
* Make the JS not stink so much in terms of formatting, classes/IDs, etc.

* Tags
    * Frontend
        * Load list from API on boot
        * Get list on pageload
        * Have endpoint to refresh API if frontend hits tag it doesn't know about (rate limited)
    * Backend approaches/search
        * Encode as raw json
            * Can't look up on tag
            * Zero effort as long as frontend returns tag list
        * Rich json field
            * Look up on tags
            * Increased database load ($$$$)
        * Explicit fields
            * Requires to limit tag count
