#include "testing/testing.h"
#include "BLI_array_cxx.h"

using namespace BLI;

TEST(array, DefaultConstructor)
{
  Array<int> array;
  EXPECT_EQ(array.size(), 0);
}

TEST(array, SizeConstructor)
{
  Array<int> array(5);
  EXPECT_EQ(array.size(), 5);
}

TEST(array, FillConstructor)
{
  Array<int> array(5, 8);
  EXPECT_EQ(array.size(), 5);
  EXPECT_EQ(array[0], 8);
  EXPECT_EQ(array[1], 8);
  EXPECT_EQ(array[2], 8);
  EXPECT_EQ(array[3], 8);
  EXPECT_EQ(array[4], 8);
}

TEST(array, InitializerListConstructor)
{
  Array<int> array = {4, 5, 6, 7};
  EXPECT_EQ(array.size(), 4);
  EXPECT_EQ(array[0], 4);
  EXPECT_EQ(array[1], 5);
  EXPECT_EQ(array[2], 6);
  EXPECT_EQ(array[3], 7);
}

TEST(array, ArrayRefConstructor)
{
  int stackarray[4] = {6, 7, 8, 9};
  ArrayRef<int> array_ref(stackarray, ARRAY_SIZE(stackarray));
  Array<int> array(array_ref);
  EXPECT_EQ(array.size(), 4);
  EXPECT_EQ(array[0], 6);
  EXPECT_EQ(array[1], 7);
  EXPECT_EQ(array[2], 8);
  EXPECT_EQ(array[3], 9);
}

TEST(array, CopyConstructor)
{
  Array<int> array = {5, 6, 7, 8};
  Array<int> new_array(array);

  EXPECT_EQ(array.size(), 4);
  EXPECT_EQ(new_array.size(), 4);
  EXPECT_NE(array.begin(), new_array.begin());
  EXPECT_EQ(new_array[0], 5);
  EXPECT_EQ(new_array[1], 6);
  EXPECT_EQ(new_array[2], 7);
  EXPECT_EQ(new_array[3], 8);
}

TEST(array, MoveConstructor)
{
  Array<int> array = {5, 6, 7, 8};
  Array<int> new_array(std::move(array));

  EXPECT_EQ(array.size(), 0);
  EXPECT_EQ(new_array.size(), 4);
  EXPECT_EQ(new_array[0], 5);
  EXPECT_EQ(new_array[1], 6);
  EXPECT_EQ(new_array[2], 7);
  EXPECT_EQ(new_array[3], 8);
}

TEST(array, CopyAssignment)
{
  Array<int> array = {1, 2, 3};
  Array<int> new_array = {4};
  EXPECT_EQ(new_array.size(), 1);
  new_array = array;
  EXPECT_EQ(new_array.size(), 3);
  EXPECT_EQ(array.size(), 3);
  EXPECT_NE(array.begin(), new_array.begin());
  EXPECT_EQ(new_array[0], 1);
  EXPECT_EQ(new_array[1], 2);
  EXPECT_EQ(new_array[2], 3);
}

TEST(array, MoveAssignment)
{
  Array<int> array = {1, 2, 3};
  Array<int> new_array = {4};
  EXPECT_EQ(new_array.size(), 1);
  new_array = std::move(array);
  EXPECT_EQ(new_array.size(), 3);
  EXPECT_EQ(array.size(), 0);
  EXPECT_EQ(new_array[0], 1);
  EXPECT_EQ(new_array[1], 2);
  EXPECT_EQ(new_array[2], 3);
}
