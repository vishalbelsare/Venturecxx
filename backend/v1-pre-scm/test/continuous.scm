(define-test (forward-normal-dist)
  (let ()
    (define samples (collect-samples `(begin ,gaussian-defn (normal 0 1))))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 0 1))) *p-value-tolerance*))))

(define-test (forward-2-normal-dist)
  (let ()
    (define samples
      (collect-samples
       `(begin
          ,gaussian-defn
          (normal (normal 0 1) 1))))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 0 (sqrt 2)))) *p-value-tolerance*))))

(define-test (unrestricted-infer-normal-dist)
  (let ()
    (define samples
      (collect-samples
       `(begin
          ,map-defn
          ,mcmc-defn
          ,gaussian-defn
          (model-in (rdb-extend (get-current-trace))
            (assume mu (normal 0 1))
            (assume y (normal mu 1))
            (infer (mcmc 10))
            (predict mu)))))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 0 1))) *p-value-tolerance*))))

(define-test (observed-normal-dist)
  (let ()
    (define samples (collect-samples (gaussian-example 20)))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2))))) *p-value-tolerance*))))

(define-test (modelling-by-inference-smoke)
  (check (> (k-s-test (collect-samples `(begin ,gaussian-by-inference-defn (my-normal 0 1)))
                      (lambda (x) (gaussian-cdf x 0 1)))
            *p-value-tolerance*)))

(define-test (modelling-by-inference)
  (check (> (k-s-test (collect-samples `(begin
                                          ,gaussian-by-inference-defn
                                          (model-in (rdb-extend (get-current-trace))
                                            (assume x (my-normal 0 1))
                                            (observe (my-normal x 1) 2)
                                            (infer (mcmc 20))
                                            (predict x))))
                      (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2)))))
            *p-value-tolerance*)))
