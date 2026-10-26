# 1381PollTax
This is the code used in a publication on the 1381 poll tax, focusing on data quality and female wealth. I am currently finishing up said publication, and I am sure that I will not forget to update this readme when I upload the manuscript.

The main file is (to be uploaded as of writing this readme). It loads in all the data in csv format, creates "person" objects for each person that contains all their info, and groups people together in their settlements, which are also objects. After this, the settlements are filtered based on the people within them as explained in the article. Then, a large amount of simulations are run to reconstruct both lost assessments and the unassessed parts of the population. Finally, most of the figures used in the article are created and saved.

A secondary file is "entropy.py". This code performs the simulations and creates the plot of Appenix A1, where the influence of assessment resolution upon the final calculated Gini factors is determined.

I regrettably cannot share the dataset used due to it falling under the copyright of the original works, namely Carolyn Fenwick's excellent three part "The Poll Taxes of 1377, 1379 and 1381", but I would be happy to discuss how to obtain it.
