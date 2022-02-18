from customer import Customer

class CustomerGroup(Customer):
    def __init__(self, timesteps, BASEYEAR, busbar):
        super().__init__(timesteps, BASEYEAR)
        self.busbar = busbar
        self.consumer_perc_list = [0.008, 0.009, 0.010, 0.023, 0.009, 0.021, 0.013, 0.002, 0.002, 0.046, 0.060, 0.021, 0.045, 0.033, 0.047, 0.029, 0.019, 0.095, 0.036, 0.018, 0.013, 0.032, 0.084, 0.025, 0.173, 0.025, 0.008, 0.049, 0.023, 0.023]
        self.baseyear_load_profile = self.get_load_profile()*self.consumer_perc_list[(self.busbar-1)]
        self.name = self.name = 'Customer '+str(self.busbar)

if __name__ == '__main__': #for test only
    timesteps = 8760
    baseyear = 2010
    energy_customers = []
    #Create 30 customers representing the 30 bus bars
    for busbar in range(1, 3):
        cust = CustomerGroup(timesteps, baseyear, busbar)
        cust.update_load_profile()
        energy_customers.append(cust)
        # print(np.sum(cust.BASEYEARLoadProfile))
