> ### "Everyone is happier when the code we interact with is clean and consistant. Even if it doesn't match your own style perfectly, consistency is the most important thing."
>*Chris Coyier*

# SASS Style Guide

*A reasonable style guide for modern SASS development.*

## <a name='TOC'>Table of Contents</a>

1. [Enforcing the rules](#rules)
1. [Whitespace](#whitespace)
1. [Formatting](#formatting)
1. [Declaration order](#declaration-order)
1. [Naming Conventions](#naming-conventions)
1. [Miscellaneous rules](#misc)
1. [Comments](#comments)

## <a name="rules">Enforcing the rules</a>

We use SCSS over SASS.

We use [Stylelint](https://stylelint.io/) to ensure that all SASS written conforms to the rules outlined in this document. Any deviation from this will result in failing tests in Circle CI. Therefore, it's important to run these tests locally first. For a full list of the configured Stylelint rules we use, see `src/.stylelintrc` in the consumer site repo.

If you think there should be any changes to these, then raise them with the team; this is designed to be easy to use for all.

## <a name='whitespace'>Whitespace</a>

Use soft tabs set to 4 spaces.

```css
/* Bad */
.selector {
..display: flex;
}

/* Good */
.selector {
....display: flex;
}
```

Place 1 space before the leading brace and place 1 space after the colon of a declaration.

```css
/* Bad */
.selector{
    position:relative;
}

/* Good */
.selector {
    position: relative;
}
```

Place an empty newline at the end of the file.

```css
/* Bad */
.selector {
    clear: both;
}
```

```css
/* Good */
.selector {
    clear: both;
}

```

**_(Note: we have an `.editorconfig` file in the repo to handle consistent spacing by default across multiple developers/code editors)_**

**[[⬆ ]](#TOC)**

## <a name='formatting'>Formatting</a>

The chosen code format ensures that code is: easy to read; easy to clearly comment; minimises the chance of accidentally introducing errors; and results in useful diffs and blames.

+ Use 1 selector per line in multi-selector rulesets
+ Use 1 declaration per line in a declaration block
+ Use lowercase, longhand hex values
+ Use single quotes `''` e.g. `input[type='checkbox']`
+ Do not specify units for zero-values e.g. `margin: 0;` and not `margin: 0rem;`
+ Do not add leading zeroes to decimal figures (`.8` instead of `0.8`)
+ Include a space after each comma in comma-separated property or function values
+ Include a semi-colon at the end of the last declaration in a declaration block
+ Place the closing brace of a ruleset in the same column as the first character of the ruleset
+ Separate each ruleset by a blank line

```css
/* Bad */
.selector-1, .selector-2, .selector-3 { display: block; font-family: helvetica,arial,sans-serif; background: #fff; background: linear-gradient(#fff,rgba(0,0,0,0.8)) }
.selector-a, .selector-b { padding: 10px }

/* Good */
.selector-1,
.selector-2,
.selector-3 {
    display: block;
    font-family: helvetica, arial, sans-serif;
    background: #ffffff;
    background: linear-gradient(#ffffff, rgba(0, 0, 0, .8));
}

.selector-a,
.selector-b {
    padding: 10px;
}
```

**[[⬆ ]](#TOC)**

## <a name='declaration-order'>Declaration order</a>

```css
.selector {
	/* Positioning */
	position
	top
	right
	bottom
	left
	z-index

	/* Display and Box Model */
	display
	align-content
	box-align
	flex-align
	grid-row-align
	align-items
	align-self
	box-flex
	box-orient
	box-gulp
	box-sizing
	flex
	flex-basis
	flex-direction
	flex-flow
	flex-grow
	flex-item-align
	flex-shrink
	flex-wrap
	flex-pack
	justify-content
	order
	float
	width
	height
	max-width
	max-height
	min-width
	min-height
	padding
	padding-top
	padding-right
	padding-bottom
	padding-left
	margin
	margin-top
	margin-right
	margin-bottom
	margin-left
	margin-collapse
	margin-top-collapse
	margin-right-collapse
	margin-bottom-collapse
	margin-left-collapse
	overflow
	overflow-x
	overflow-y
	overflow-wrap
	clip
	clear

	/* Typography */
	font
	font-family
	font-size
	font-style
	font-weight
	hyphens
	src
	line-height
	letter-spacing
	word-spacing
	font-smoothing
	color
	text-align
	text-decoration
	text-indent
	text-overflow
	text-fill-color
	text-rendering
	text-size-adjust
	text-shadow
	text-transform
	word-break
	word-wrap
	white-space
	vertical-align
	list-style
	list-style-type
	list-style-position
	list-style-image
	pointer-events
	cursor

	/* Background */
	background
	background-attachment
	background-color
	background-image
	background-position
	background-repeat
	background-size
	filter

	/* Misc */
	border
	border-collapse
	border-top
	border-right
	border-bottom
	border-left
	border-color
	border-image
	border-top-color
	border-right-color
	border-bottom-color
	border-left-color
	border-spacing
	border-style
	border-top-style
	border-right-style
	border-bottom-style
	border-left-style
	border-width
	border-top-width
	border-right-width
	border-bottom-width
	border-left-width
	border-radius
	border-top-right-radius
	border-bottom-right-radius
	border-bottom-left-radius
	border-top-left-radius
	border-radius-topright
	border-radius-bottomright
	border-radius-bottomleft
	border-radius-topleft
	content
	quotes
	outline
	outline-offset
	opacity
	visibility
	size
	zoom
	transform
	transform-origin
	box-shadow
	table-layout

	/* Animations & Transitions */
	animation
	animation-delay
	animation-duration
	animation-iteration-count
	animation-name
	animation-play-state
	animation-timing-function
	animation-fill-mode
	tap-highlight-color
	transition
	transition-delay
	transition-duration
	transition-property
	transition-timing-function
	background-clip
	backface-visibility

	/* Misc */
	resize
	appearance
	user-select
	interpolation-mode
	direction
	marks
	page
	page-break-after
	set-link-source
	unicode-bidi
}
```

### When should I use `!important`?
Never.
*sigh*

**[[⬆ ]](#TOC)**

## <a name='naming-conventions'>Naming Conventions</a>

We use [BEM](http://getbem.com/) (Block, element, modifier) for our class naming conventions.


### Class names in React components

For our React components, each selector in a component `.scss` file will start with the name of the component followed by the class name. For example, if we were creating a green button class in a container called `JoinComponent`, the class selector would be:


```
.JoinComponent-button--green {

}
```

All code should be lowercase unless a react component name contains capitals: This applies to element names, attributes, attribute values, selectors, properties and property values.

**_(Note: for more info on our approach to handling SASS for react components, see our [Styleguide](https://octopus.energy/_styleguide))_**

```css
/* Bad */
BODY {
    margin: 0;
}

/* Good */
body {
    margin: 0;
}

.JoinComponent-button--green {
	margin: 0;
}
```

**[[⬆ ]](#TOC)**


## <a name='misc'>Miscellaneous rules</a>

Most of these are fairly obvious, but are also part of the Stylelint tests and so are worth mentioning.

+ There should never be duplicate selectors in a file
+ There should be an empty line after each selector
+ There shouldn't be any empty selectors in a file
+ There should never be more than two empty lines in a file
+ There shouldn't be any end-of-line whitespace (editorconfig takes care of this)
+ There should always be spaces between selector combinators i.e. `.foo + bar` and not `.foo+bar`

**[[⬆ ]](#TOC)**


## <a name='comments'>Comments</a>

```css
/* -----------------------------------------------------------------------------
 * Section block
 * -------------------------------------------------------------------------- */

/* Sub-section comment block
   ===================================== */

/* Basic comment */
```

**Example**:

```css
/* ==========================================================================
   Typography
   ========================================================================== */

p {
    margin: 0 0 20px;
    font-size: 16px;
}

/* Headings
   ===================================== */

h1,
h2,
h3,
h4,
h5,
h6 {
    margin: 0 0 20px;
    font-family: serif;
    font-weight: bold;
}

/* A specific fix for a thing because reasons */
.foo {
    ...
}
```

**[[⬆ ]](#TOC)**
