public class CountOnes {
	public static void main(String[] args) {
		
		int num, counter, bit, position, i;
		num = 0xf0f0f0f0;
		counter = 0;
		position = 1;
		for (i = 0; i < 32; i++) {
			bit = num & position;
			if (bit != 0)
				counter++;
			position = position << 1;
		}
		System.out.println(counter);
	}
}