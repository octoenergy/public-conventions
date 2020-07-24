# TypeScript

Type System:

- [Prefer types to interfaces](#prefer-types-to-interfaces)
- [Prefer type declarations to type assertions](#prefer-type-declarations-to-type-assertions)
- [Be DRY with types](#be-dry-with-types)

Type Inference:

- [Narrow down types](#narrow-down-types)

## Type System

### Prefer types to interfaces

The _interface_ and _type_ alias are equivalent in most ways bar a few.

The _type_ alias is preferred due to the syntax.

```ts
interface X { x: number }
interface 2D extends X { y: number }
```

```ts
type X = { x: number }
type 2D = X & { y: number }
```

Unlike the _interface_ alias, The _type_ alias can also be used for other types
such as _primitives_, _unions_, and _tuples_.

```ts
// primitive
type Name = string

// union
type Animal = Cat | Dog

// tuple
type Items = [number, string]
```

The only use case for the _interface_ alias should be
[declaration merging](https://www.typescriptlang.org/docs/handbook/declaration-merging.html).

### Prefer type declarations to type assertions

```ts
type Car {
    brand: string
}

// Type declaration
const ford: Car = {
    brand: 'Ford'
}

// Type assertion
const mazda = {
    brand: 'Mazda'
} as Car
```

TypeScript will not flag the following error when using _type assertions_ due
to the type checker thinking the code has a better understaning of the types
than it does.

```ts
const mazda = {} as Car // Silent error
```

### Be DRY with types

Avoid repeating types
```ts
function createUser(name: string, age: number) {
    // ...
}

function updateUser(name: string, age: number) {
    // ...
}
```

If the arguments are part of a collection,
create a type for the collection to avoid repeating types

```ts
type User = {
    name: string,
    age: number
}

function createUser(user: User) {
    // ...
}

function updateUser(user: User) {
    // ...
}

const MyComponent = (user : User) => {
    // ...
}

or

function createUser({ name, age } : User) {
    // ...
}

const MyComponent = ({ name, age } : User) => {
    // ...
}
```

#### Factor out the type for functions with common signatures

Abstract the type for functions with common signatures

Instead of
```ts
const get = (url: string, options: Options): Promise<Response> => { //... }
const post = (url: string, options: Options): Promise<Response> => { //... }
```

Prefer
```ts
type HTTPFunction = (url: string, options: Options): Promise<Response>
const get: HTTPFunction = (url, opts) => { //... }
const post: HTTPFunction = (url, opts) => { //... }
```

#### use type operations and generics

read "extends" as "subset of"

## Type Inference

### Narrow down types

#### Use `const` to narrow down types

```ts
let x: number = 9 // Type is number
```

Write
```ts
let x = 9 // Type is number
```

Hovering over the x in your editor will show that the type has been inferred as a number. The explicit annotation is redundant.

Type inference is not solely based on the value but also the context

Here TypeScript infers a type that might be more precise then what you might expect. Variables declared with `const`

```ts
const x = 9 // Type is "x"
```

```ts
const x: number = 9 // Type is number
```

#### Use `readonly` to narrow down types in objects

#### Use type guards to narrow down types in predicates

TypeScript can have difficulty inferring types in array functions.
```ts
const numbers = ["cherry", "lemon", 5, 1]
                .filter(item => typeof(item) == 'number') // Type is (string | number)[]
```

Type guards can be used to narrow the return type.
```ts
function isNumber(x: number | string): x is number {
    return typeof(item) == 'number'
}

const numbers = ["cherry", "lemon", 5, 1]
                .filter(isNumber) // Type is number[]
```


### Acknowledgements

Many shoutouts to [Effective TypeScript](https://github.com/danvk/effective-typescript)
for being the inspiration behind many of these conventions.
