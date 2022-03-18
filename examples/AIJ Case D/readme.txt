This is a guide on how to make use of the scripts to generate the plots (Wind Speed comparison , correlation plots , TKE, etc..)

The scripts falls into two categories: 
	1) 0 degree wind direction (3 scripts):
			1) AIJ_Case_D_result_comparison. (To compare the velocity from SimScale and the validation case)
			2) TKE_API. (To compare the TKE profile from SimScale and the validation case)
			3) ABL_comparison_probe.(To compare the "target", "Probe" and "Experiment" ABL and TKE profiles)
				note: Here target refers to the profiles at the inlet. 
				           probe  refers to the profiles at the predefined probe points in the simulation. 

	2) other wind directions (e.g. 45 degrees)
			1)AIJ_Case_D_result_comparison_directions. 


1)The process provided here is in relation to the 0 degree wind direction (The setup is the same for the other directions): 
	1.1 For all scripts you need to modify the following in order for to locate your project and data via the API: 
		1) Project name      --> result.find_project ("Project Name")
		2) Simulation name   --> result.find_simulation ("Simulation Name")
		3) Run name          --> result.find_run ("Run Name")
		4) Probe Points name --> e.g. : name = "Validation points". (This is the name of the probe points parameter you used in your simulatoin setup)
		
	1.2 Experimental data: 
		1) Provide the path  --> experimental_path = ... (Make sure to have the excel file in the same directory where the scripts are located, otherwise modify the part of the code accordingly)
		2) Make sure to specify the right column of your experimental results excel file to the plot data: 
			- For example you uploaded an excel file of your experimental results in the form: 
				Item 		U/U_ref

			- in the plot method you would notice the following: 
				experimental_results[U/U_ref] which means that the column U/U_ref is used for comparison. 
				

	1.3 Regarding ABL_comparison_probe script: 
		- Inside the SimScale workbench, provide an excel file that contains the coordinates of the probe points where you want to visualize the ABL and TKE profiles. 
		- Make sure that these Probe Points are aligned with the wind direction that you are simulating. 
			