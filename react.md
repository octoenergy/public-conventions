# React documentation

## ESLint Configuration

Recommended eslint configration is used

```
"plugin:react/recommended"
```

The rules enabled in this configuration are:

- [react/display-name](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/display-name.md)
- [react/jsx-key](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/jsx-key.md)
- [react/jsx-no-comment-textnodes](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/jsx-no-comment-textnodes.md)
- [react/jsx-no-duplicate-props](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/jsx-no-duplicate-props.md)
- [react/jsx-no-target-blank](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/jsx-no-target-blank.md)
- [react/jsx-no-undef](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/jsx-no-undef.md)
- [react/jsx-uses-react](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/jsx-uses-react.md)
- [react/jsx-uses-vars](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/jsx-uses-vars.md)
- [react/no-children-prop](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-children-prop.md)
- [react/no-danger-with-children](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-danger-with-children.md)
- [react/no-deprecated](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-deprecated.md)
- [react/no-direct-mutation-state](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-direct-mutation-state.md)
- [react/no-find-dom-node](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-find-dom-node.md)
- [react/no-is-mounted](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-is-mounted.md)
- [react/no-render-return-value](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-render-return-value.md)
- [react/no-string-refs](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-string-refs.md)
- [react/no-unescaped-entities](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-unescaped-entities.md)
- [react/no-unknown-property](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/no-unknown-property.md)
- [react/prop-types](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/prop-types.md)
- [react/react-in-jsx-scope](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/react-in-jsx-scope.md)
- [react/require-render-return](https://github.com/yannickcr/eslint-plugin-react/blob/HEAD/docs/rules/require-render-return.md)

## Testing

### Integration testing

Containers should have intregration tests that fully mount the component and test the main functionality of the container and child
components.

Discretion is required as to whether a class component requires an integration test. If it is capable of altering the state of the store
then it is advised to mount the component with a proper store.

### Unit testing

All functional and class components should have simple unit tests which successfully shallow mount the components.

# Redux

## Testing

### Black-box testing

In order to more accurately simulate the behaviour of the application being tested, the applications's actions, reducers, and selectors
should be tested together.

We do this by dispatching actions to the store, and querying the state using selectors. Verifying the outcome using the selectors is
a way of covering all three aspects in a single pass. The reducers are implicitly tested.

#### Format

The format of these tests are as follows:

##### Create a store from the combined reducer

```
import { createStore } from 'redux'
import combinedReducer from './reducers'

const store = createStore(combinedReducer)
```

##### Dispatch actions to the store using action creators

```
import * actions from './actions'

store.dispatch(actions.add(something));
```

#### Query the store using a selector

```
import * selectors from './selectors'

const state = store.getState()
const somethingFromStore = selectors.somethingSelector(state)

expect(somethingFromStore).toBe(something)
```