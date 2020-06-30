# GraphQL

Reponses:

- [How to understand errors](#how-to-understand-errors)

Mutations:

- [Begin names with action type](#begin-names-with-action-type)
- [Use an input object type for the argument](#use-an-input-object-type-for-the-argument)
- [Return an object in the payload](#return-an-object-in-the-payload)
- [Return all errors at the top-level](#return-all-errors-at-the-top-level)

## Responses

### How to understand errors

Unlike a conventional REST API, GraphQL APIs do not rely on HTTP status codes to signal request outcomes.
Our GraphQL API always return a JSON body with the 200 status code, even when there are errors.

If an error occurred, the response body MUST include a top-level errors array that describes the error or errors as demanded by the [GraphQL spec](https://spec.graphql.org/June2018/#sec-Response-Format).

Errors can manifest as GraphQL validation errors (e.g. provided a string for an integer field), Kraken validation errors (e.g. invalid direct debit card number), or errors reflecting upstream issues.

```json
{
   "errors":[
      {
         "message": "Could not find property",
         "locations":[
            {
               "line": 3,
               "column": 9
            }
         ],
         "path":[
            "property"
         ],
         "extensions":{
            "errorClass": "NOT_FOUND",
         }
      }
   ],
   "data":{
      "property": null
   }
}
```

An element of the errors array follows the [GraphQL spec](https://graphql.github.io/graphql-spec/June2018/#sec-Errors) and will have the following values:

- `message`: The human-readable error message. This value is not intended to be parsed and may change at any time.
- `locations`: An array of { "line": x, "column": y } objects that describe where the error was detected during parsing of the 
- GraphQL query. This is typically only used by interactive viewers such as GraphiQL, including our API Explorer.
- `path`: The GraphQL query or mutation causing the error.
- `extensions`: Additional information about the error
   - `errorClass`: [The class of the error](#error-classes). 

For queries, it is possible to have partially successful responses, where both a partially populated data object and errors are returned. If errors prevent a field in your query from resolving, the field in the data object will be returned with the value null and relevant errors will be in the error object.

#### Error classes

##### AUTHORIZATION

Queries, Mutations: User access unauthorised

##### NOT_FOUND

Queries: Resource could not be found
Mutations: Resource to update could not be found (E.g invalid id provided)

##### NOT_IMPLEMENTED

Queries, Mutations: Feature not implemented yet

##### SERVICE_AVAILABILITY

Queries, Mutations: An intermittent error due to an unavailable service

##### VALIDATION

Mutation: Validation error due to invalid input(s)

- `validationErrors`: All validation errors
   - `inputPath`: The input field responsible for the error (Optional)
   - `message`: The human-readble error message

```json
{
   "errors":[
      {
         "message": "Invalid inputs",
         "locations":[
            {
               "line": 3,
               "column": 9
            }
         ],
         "path":[
            "createUser"
         ],
         "extensions":{
            "errorClass": "VALIDATION",
            "validationErrors":[
               {
                  "inputPath":[
                     "input",
                     "user",
                     "firstName"
                  ],
                  "message": "Name too short"
               },
               {
                  "inputPath":[
                     "input",
                     "user",
                     "age"
                  ],
                  "message": "Not a number"
               }
            ]
         }
      }
   ],
   "data":{
      "createUser":"None"
   }
}
```

No `inputPath` should be provided for validation errors where the inputs are valid individually but a combination of them are invalid (E.g direct debit details account number and sort code are individually valid but invalid together)

```json
{
   "errors":[
      {
         "message": "Invalid inputs",
         "locations":[
            {
               "line": 3,
               "column": 9
            }
         ],
         "path":[
            "createUser"
         ],
         "extensions":{
            "errorClass": "VALIDATION",
            "validationErrors":[
               {
                  "message": "Invalid direct debit details"
               }
            ]
         }
      }
   ],
   "data":{
      "createUser":"None"
   }
}
```

## Mutations

### Begin names with action type

✅
```gql

mutation CreateUserMutation($input: UserInputType!) {
   createUser(input: $input) {
       user {
           firstName
       }
   }
}
```

where

```
type User {
  firstName: String!
  lastName: String!
  age: Int!
}
```

✅
```gql

mutation DeleteUserMutation($input: UserInputType!) {
   deleteUser(input: $input) {
       user {
           firstName
       }
   }
}
```

### Use an input object type for the argument

✅
```gql

mutation UpdateUserMutation($input: UserInputType!) {
   updateUser(input: $input) {
       user {
           firstName
       }
   }
}
```

where 

```
type UserInputType {
    firstName: String!
    lastName: String!
    age: Int!
}

```

❌
```gql
mutation UpdateUserMutation($firstName: String!, $lastName: String!, $age: Int!) {
   updateUser(firstName: $firstName, lastName: $lastName, age: $age) {
       user {
           firstName
       }
   }
}
```

Otherwise the mutations become more cumbersome to write out as the number of arguments grow
Input object types are more flexible to changes. If the arguments change, less places need to be updated
In the case where different mutations have the same arguments, the input object type can be reused.

```gql
mutation CreateUserMutation($input: UserInputType!) {
   createUser(input: $input) {
       user {
           firstName
       }
   }
}
```

### Return an object in the payload

Ideally the object you've mutated
If the returned object has the same global id as one stored in the apollo client cache,
the UI using this data will be automatically updated with the latest data.
[Source](https://www.freecodecamp.org/news/how-to-update-the-apollo-clients-cache-after-a-mutation-79a0df79b840/)

✅
```gql
mutation UpdateUserMutation($input: UserInputType!) {
   updateUser(input: $input) {
       user {
           id
           firstName
           lastName
       }
   }
}
```

❌
```gql
mutation UpdateUserMutation($input: UserInputType!) {
   updateUser(input: $input) {
        firstName
        lastName
   }
}
```

