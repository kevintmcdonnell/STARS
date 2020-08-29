public class SelectionSort {
	/** The method for sorting the numbers */
	public static void selectionSort(int[] array) {
		for (int i = 0; i < array.length - 1; i++) {
			// Find the minimum in the array[i..array.length-1]
			int currentMin = array[i];
			int currentMinIndex = i;

			for (int j = i + 1; j < array.length; j++) {
				if (currentMin > array[j]) {
					currentMin = array[j];
					currentMinIndex = j;
				}
			}

			// Swap array[i] with array[currentMinIndex] if necessary;
			if (currentMinIndex != i) {
				array[currentMinIndex] = array[i];
				array[i] = currentMin;
			}
		}
	}
}
