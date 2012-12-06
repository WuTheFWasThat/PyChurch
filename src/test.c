#include <stdio.h>
      
int main()
{
        int i, sum = 0;
       
        for ( i = 1; i <= LAST; i++ ) {
          sum += i;
        }
        printf("sum = %d\n", sum);

        return 0;
}
