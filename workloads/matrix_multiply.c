
#include <stdio.h>

#define N 128

double A[N][N];
double B[N][N];
double C[N][N];

int main() {

    // Initialize matrices
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = (i + j + 1) * 0.5;
            B[i][j] = (i - j + 2) * 0.25;
            C[i][j] = 0.0;
        }
    }

    // Matrix multiplication
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }

    printf("Matrix Multiplication: %d x %d\n", N, N);
    printf("C[0][0] = %.4f\n", C[0][0]);
    printf("C[127][127] = %.4f\n", C[127][127]);

    printf("Matrix multiplication completed successfully.\n");

    return 0;
}
