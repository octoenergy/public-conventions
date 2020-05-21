# GraphQL

Mutations:

- [Begin names with action type](#begin-names-with-action-type)
- [Use an input object type for the argument](#use-an-input-object-type-for-the-argument)
- [Return an object in the payload](#return-an-object-in-the-payload)
- [Return all errors at the top-level](#return-all-errors-at-the-top-level)
- [Return validation errors in extensions](#return-validation-errors-in-extensions)

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

### Return all errors at the top-level

All errors should be returned as top-level errors as stated in the [graphql specification](https://spec.graphql.org/June2018/#sec-Response-Format)

### Return validation errors in extensions

These are defined by the `errorClass` `VALIDATION`
Should return a `validationErrors` field in `extensions`.
Each error should contain the path to the input which caused the error.

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
