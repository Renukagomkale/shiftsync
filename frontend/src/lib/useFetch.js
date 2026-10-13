import { useCallback, useEffect, useRef, useState } from "react";

export default function useFetch(load, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const latest = useRef(0);

  const run = useCallback(() => {
    const id = ++latest.current;
    setState((current) => ({ ...current, loading: true, error: null }));
    return load()
      .then((data) => id === latest.current && setState({ data, loading: false, error: null }))
      .catch((error) => id === latest.current && setState({ data: null, loading: false, error }));
  }, deps);

  useEffect(() => {
    run();
  }, [run]);

  return { ...state, reload: run };
}
