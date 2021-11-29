## TODO

- [ ] Change the colors 
  - Muted colors?
- [ ] Intagrate the colors as CSS variables
- [ ] Adjust sizing of button elements
  - Larger seems distracting, too small is harder to use on mobile (e.x iPad or a Surface Tablet)
- [ ] Remove or reduce usage of borders
  - [ ] Test different colored borders
  - [ ] Test the sizing of borders 1pt or 2pt
- [ ] Play around with the border radius, prehaps try 4pt over 6pt 
- [ ] Try setting the transparency to 95% or somthing in that range
- [ ] Play with the sizing of text (Right now it is a tiny bit too large)
  - [ ] Have the player behave more as a cover image
    - The player needs to be the main focus, right now the title takes that place, then the hilighted buttons take second over the player. 
- [ ] Remove visual "noise"
  - [ ] Remove shadows (It is too much)
  - [ ] Remove the bold borders 
    - They compete for attention and are distracting
  - [ ] Try a different base font size, 12pt over 14pt?
  - [ ] Adjust the weird spacing issues in Firefox
  - [ ] Do cross-browser testing
    - [ ] Firefox
    - [ ] Firefox with the Safest Settings
    - [ ] Brave
    - [ ] Brave on the Safest Settings
    - [ ] Google Chrome
    - [ ] Ungoogled Chromium
    - [ ] Ungoogled Chromium with Ublock origin
    - [ ] Safari
    - [ ] Microsoft Edge

## Planned 

- [ ]  Add a defined section for the footer
- [ ] Define a section for the "last watched streams" 
- [ ] Add a heart "<3" to the "Made with open source and love" section (I think it would be cute hehe)

## Maybe

- [ ] Player cover option
  - This option if toggled would have the player cover most of the UI, toggling this would add the class cover to the main html tag allowing for styling in css, by having this people who want a more "Movie Theater like" experence can get that. 
- [ ] A custom logo image? Text is a bit harder for me to keep consistent
- [ ] Adding a light theme 
  - This may be somthing I could add, but as of now I find a light theme distracting, especally after trying a basic one out, it is too much...
- [ ] Change the emoticon in the footer to an emoji (Twimoji)
- [ ] Custom option box's
- [ ] Custom styled text fields
- [ ] I *can* test it in old edge (The one using EdgeHTML) and Internet explorer 11, but I don't wanna. 

## Known issues

- [ ] Margin and padding are not set on some elements, leading to odd spacing depending on the browsers defaults, a temporary fix could be to use `* {padding: 0; margin: 0}` in the css, but that is not a good fix.
- [ ] Grid transition is not smooth, I will eventually transition from a grid of four to three and then to two, but so far I have not gotten to that
- [ ] Selecting an element in Firefox Mac creates a shadow (I could probably hide that and add my own selection indacator?) 

