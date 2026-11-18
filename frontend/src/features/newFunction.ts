/** Turn the new function on in a test build with REACT_APP_FEATURE_NEW_FUNCTION=true. */
export const newFunctionEnabled =
  process.env.REACT_APP_FEATURE_NEW_FUNCTION === "true";
