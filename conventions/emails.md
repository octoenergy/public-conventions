# Email documentation

## Templates

### Default (template.html)
This is the standard style for our emails and matches the brand of our consumer site.

#### Blocks
**title [text only]** - The title of the email (not shown in the actual HTML)

**preview-text [text only]** - A hidden HTML element at the start of the email. This is shown underneath the subject line of an email in a users  inbox and should reflect what is happening in the email

**query_width [pixel value - default 600px]** - the value at which mobile styles kick in on platforms that support it.

**content_width [number - default 600]** - The container width of the email. This should make the value of query_width but as a number instead of a pixel value.

**footer_width [number - default 600]** - The footer width of the email. This should make the value of query_width but as a number instead of a pixel value.

**extrastyles-mobile [CSS selectors]** - Any mobile-specific styles for the email

**extrastyles [CSS selectors]** - Any new styles specific to the email

**notifications [HTML]** - An area at the top of the email to display a notification to the user. Example contents:
```
<tr>
    <td bgcolor="#27b1f9">
        <table width="600" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 0 auto; color: #000000; background-color: #27b1f9;" class="table">
            <tr>
                <td>
                    <table width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tr><td colspan="3" height="10" bgcolor="#27b1f9" style="background-color: #27b1f9;"></td></tr>
                        <tr>
                            <td align="left" class="mobile-bumper" width="30"></td>
                            <td align="center" style="{{ font }} font-size: 12px; line-height: 16px;">
                                // NOTIFICATION CONTENT
                            </td>
                            <td align="left" class="mobile-bumper" width="30"></td>
                        </tr>
                        <tr><td colspan="3" height="10" bgcolor="#27b1f9"></td></tr>
                    </table>
                </td>
            </tr>
        </table>
    </td>
</tr>
```

**top-padding [number - default 50]** - An HTML row to add padding above email content, who’s height you can alter.

**header [HTML]** - An area to add a header/title for an email. Sits inside a `<tr>` tag, so appropriate HTML inside the tag would be:
```
<td class="text" style="font-size: 18px; line-height: 24px; color: {% email_text_colour recipient %}; font-weight: 300;">
    // CONTENT
</td>
```

**breakout [HTML]** - A wrapper for the breakout_content block that displays content in an info-style box for emphasis. If you don’t want to use this in an email, you should add an empty block like so:
`{% block breakout %}{% endblock %}`

**layout [HTML]** - Change this to alter the core layout of the email (not recommended)

**container_content [HTML]** - A chance to add custom HTML just above the content block. As the content block is designed to be just text, use this to add something a bit more complex should you need to. The block is inside a `<table>` tag and so any content you add should start with a `<tr>`

**content_styles [inline CSS]** - Use this to change the style of the main content text.

**content [text]** - The main body of the email. Use only text, spans, and simple `<br/>` tags here.

**signoff [text - default ‘Love and power’]** - Use if you’d like to change the sign-off.

**sender [text - default ‘The Octopus Energy team’]** - Use if you’d like to change the sender name.

**ps [HTML]** - A chance to add custom HTML just above the content block. This block is inside a `<table>` tag so any content in this block should start with a `<tr>` tag.

**logo [HTML]** - Use this if you’d like to change the logo in the email footer. By default this block contains two `<div>` tags, with one containing an SVG image for platforms that can support it, and a PNG fallback. For an example of the markup, just the `template.html` file.

#### Inverting colours
This template changes its colour scheme based on a users preference, as some have issues reading white text on a black background. To accomplish this, we have three variables inside the template:
`{% email_background_colour recipient %}` - for the correct background colour
`{% email_text_colour recipient %}`  - for the correct text colour
`{% email_breakout_colour recipient %}` - for the correct breakout border/background colour.

If you would like to add something specific for those who have (or have not) opted to invert their comms colours, you can use:
```
{% if not recipient.use_inverted_email_colours %}
    //
{% endif %
```

### Letter template (template-letter.html)
This email is styled like a simple letter (black text on a white background). The style is used exclusively for our welcome emails, either direct or from third parties.

#### Blocks
**title [text only]** - The title of the email (not shown in the actual HTML)

**preview-text [text only]** - A hidden HTML element at the start of the email. This is shown underneath the subject line of an email in a users  inbox and should reflect what is happening in the email.

**extrastyles-mobile [CSS selectors]** - Any mobile-specific styles for the email.

**extrastyles [CSS selectors]** - Any new styles specific to the email.

**content [text]** - The main body of the email. Use only text, spans, and simple `<br/>` tags here.

**signoff [text - default ‘Love and power’]** - Use if you’d like to change the sign-off.

**ps [HTML]** - Use this block to ad a PS. This block is inside a `<table>` tag so any content in this block should start with a `<tr>` tag.

### Intercom template (template-intercom.html)
This template mirrors the style of Intercom’s emails, as our users are used to receiving communications in this style. Most commonly, this style is used for ad-hoc marketing emails through Sendgrid, but is also used occasionally for Kraken communications.

#### Blocks
**content [text]** - The main body of the email. Use only text, spans, and simple `<br/>` tags here.

**signoff [text]** - Use if you’d like to change the sign-off.

**ps [HTML]** - Use this block to ad a PS. This block is inside a `<table>` tag so any content in this block should start with a `<tr>` tag.

**footer-image [text]** - The `src` attribute of the image at the bottom of the email. By default, it’s an image of Pete Miller.

**footer-signoff [text]** - The first name of the person the email is from.

## Ad hoc emails
We frequently send marketing emails to our users separate to those sent through the site.  These are made on the fly and usually overseen by Pete Miller.

### Sendgrid
The platform we use to send these emails is Sendgrid, the details for which are in 1password. All emails are stored in Marketing > Campaigns. 

#### Merge fields
All dynamic data in Sendgrid is handled via a CSV, where you can pick a name for each column. Once this is done, the syntax for adding a merge field is [% MERGE_FIELD_NAME %]. You can test this is working correctly by sending a test email to yourself in Sendgrid with data for your email address populated.

### Yeoman generator
A generator using Yeoman has been created to make building, editing, and generating emails as quickly as possible. Once installed, you will be able to run `yo email` in a directory to build an email and dev environment from scratch, and will offer to add to the source code an example of the following for easy reproduction:
• Title
• Breakout box
• CTA button

The generator is based on [Foundation for Emails 2 Docs](https://foundation.zurb.com/emails/docs/)

This framework handles weird platform hacks/eccentricities automatically, and allows you to use standard HTML in the email and it’ll convert it. It also has some built in helper tags (in their custom language called ink) to handle things like grids with columns, buttons, and centring content, which are typically tricky to handle in emails.

The dev environment also has:
• Live reload so every change to the source files updates the page you’re working on
• Allows you to handle styles separately  in `.scss` files and, when building for production, inlines all the styles into the correct tags.
• HTML minifying to reduce page bloat and prevent whitespace issues that often occur.

The base template in this generator has already tested so there’s no need to worry about extensive testing (just standard litmus to make sure).

Right now this is only available in the style of the standard consumer site emails, but Ashley will be working on adding the Intercom style in the near future.

The repo for this can be found at:
[octoenergy Github - email generator repo](https://github.com/octoenergy/email-generator)


## Testing
Due to the volatility of different email platforms, it is important to test every email cross-platform before sending it.

### Litmus
Litmus is an email testing service, the details for which you can find in 1password. You can test your email here by inserting the HTML in directly, or emailing an email to octopusenergy@litmustest.com

They also have a ‘builder’ feature you can use, where you can make changes to the markup and see live previews of how the email will render in certain email platforms.