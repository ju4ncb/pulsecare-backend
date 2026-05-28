# Entrenamiento y validación - 2026-05-28T21:08:18.223627+00:00

## Resultado de entrenamiento (test split)
- Muestras totales usadas: 90
- Accuracy: 0.9130
- Precision: 0.9304
- Recall: 0.9130
- F1: 0.9148

### Matriz de confusión (train test split)
```
[
  [
    6,
    1,
    0
  ],
  [
    0,
    8,
    0
  ],
  [
    0,
    1,
    7
  ]
]
```

### Classification report (train test split)
```
{
  "0": {
    "precision": 1.0,
    "recall": 0.8571428571428571,
    "f1-score": 0.9230769230769231,
    "support": 7.0
  },
  "1": {
    "precision": 0.8,
    "recall": 1.0,
    "f1-score": 0.8888888888888888,
    "support": 8.0
  },
  "2": {
    "precision": 1.0,
    "recall": 0.875,
    "f1-score": 0.9333333333333333,
    "support": 8.0
  },
  "accuracy": 0.9130434782608695,
  "macro avg": {
    "precision": 0.9333333333333332,
    "recall": 0.9107142857142857,
    "f1-score": 0.9150997150997151,
    "support": 23.0
  },
  "weighted avg": {
    "precision": 0.9304347826086956,
    "recall": 0.9130434782608695,
    "f1-score": 0.9147528799702712,
    "support": 23.0
  }
}
```

## Validación sobre dataset etiquetado completo
- Muestras: 90
- Accuracy: 0.9778
- Precision: 0.9792
- Recall: 0.9778
- F1: 0.9779

### Matriz de confusión (validación full)
```
[
  [
    29,
    1,
    0
  ],
  [
    0,
    30,
    0
  ],
  [
    0,
    1,
    29
  ]
]
```

### Classification report (validación full)
```
{
  "0": {
    "precision": 1.0,
    "recall": 0.9666666666666667,
    "f1-score": 0.9830508474576272,
    "support": 30.0
  },
  "1": {
    "precision": 0.9375,
    "recall": 1.0,
    "f1-score": 0.967741935483871,
    "support": 30.0
  },
  "2": {
    "precision": 1.0,
    "recall": 0.9666666666666667,
    "f1-score": 0.9830508474576272,
    "support": 30.0
  },
  "accuracy": 0.9777777777777777,
  "macro avg": {
    "precision": 0.9791666666666666,
    "recall": 0.9777777777777779,
    "f1-score": 0.9779478767997084,
    "support": 90.0
  },
  "weighted avg": {
    "precision": 0.9791666666666666,
    "recall": 0.9777777777777777,
    "f1-score": 0.9779478767997085,
    "support": 90.0
  }
}
```

Modelo guardado en: `artifacts\risk_model.pkl`