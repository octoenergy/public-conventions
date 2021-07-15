# Shorthand

This pages explains what the emojis used in code-review comments and Slack mean.
They are shorthand for common situations.

## In code review comments

### 💬 - debug code... 
Debug/commented-out code needs removing/uncommenting

### 👻, 🕵🏾, 🐼 - pedantry...
Minor/pedantic point - short hand for:
> "I know this this is deeply pedantic but..."). 

For comments so pedantic you're almost embarrassed to write them, wrap in `<sup>` tags.

> 🐼<sup>"Direct Debit" should be title-case.</sup>

"Panda-ntic" if you will.

### 👀 - please look at this...
Please eyeball this change/commit/code:
> 👀 Hey @team, is this change ok? I'm not that familiar with $domain_concept

### ♻️  - same as above... 
Same explanation as above (aka ditto)

### 🐂, 🐃 - out-of-scope, but...
Yak-shaving code review comments, as in:

> I know this is out of scope for this PR request but ...

or something like:

> I know you only renamed the file but I'm going to comment on all the green lines in the diff that you didn't write...

## In Slack

✅ - PR approved

🏓 - "I've requested changes" or "I've responded to your feedback" (back to you...)

💬 - comments added

🚢 - PR merged (aka shipped)

🏀 - PR can be merged immediately after passing review (ie a "slam dunk" or, more accurately, an "alley oop")
