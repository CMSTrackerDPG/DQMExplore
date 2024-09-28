import numpy as np
from dqmexplore.me_ids import meIDs1D, meIDs2D
import warnings


class MEData:
    def __init__(self, me_df):
        self.me_dict = {}
        self._generate_me_dict(me_df)

    def _generate_me_dict(self, me_df):
        if len(me_df) == 0:
            warnings.warn("Input DataFrame is empty.")
        mes = list(me_df["me"].unique())

        for me in mes:
            self.me_dict[me] = {}

            sorted_dfsubset = me_df[me_df["me"] == me].sort_values(by="ls_number")
            me_id = sorted_dfsubset["me_id"].unique()[0]
            if me_id in meIDs1D:
                dim = 1
            elif me_id in meIDs2D:
                dim = 2
            else:
                raise ValueError("Unrecognized monitoring element id number")

            data_arr = np.array(sorted_dfsubset["data"].to_list())
            entries = np.array(sorted_dfsubset["entries"].to_list())

            self.me_dict[me]["x_bins"] = np.linspace(
                sorted_dfsubset["x_min"].iloc[0],
                sorted_dfsubset["x_max"].iloc[0],
                int(sorted_dfsubset["x_bin"].iloc[0]),
            )

            if dim == 2:
                self.me_dict[me]["y_bins"] = np.linspace(
                    sorted_dfsubset["y_min"].iloc[0],
                    sorted_dfsubset["y_max"].iloc[0],
                    int(sorted_dfsubset["y_bin"].iloc[0]),
                )

            self.me_dict[me]["me_id"] = me_id
            self.me_dict[me]["dim"] = dim
            self.me_dict[me]["data"] = data_arr
            self.me_dict[me]["entries"] = entries
            # self.me_dict[me]["integral"] = None
            # self.me_dict[me]["norm"] = None
            # self.me_dict[me]["trignorm"] = None
        self._setEmptyLSs()
        self.excludelumis = []
        self.numLSs = len(self.getData(self.getMENames()[0]))

    def __getitem__(self, me):
        return self.me_dict[me]

    def __len__(self):
        return len(self.me_dict)

    def getData(self, me, ls=None, type="data"):
        if ls is not None and not isinstance(ls, int):
            raise TypeError("LS should either be None or a positive integer.")

        if (ls is not None) and (type == "integral"):
            raise ValueError("Cannot select LS in integrated data.")

        if ls is None:
            return self.me_dict[me][type]
        else:
            return self.me_dict[me][type][ls - 1]

    def getNumLSs(self):
        return self.numLSs

    def getEntries(self, me):
        return self.me_dict[me]["entries"]

    def getBins(self, me, dim="x"):
        if dim == "x":
            return self.me_dict[me]["x_bins"]
        elif dim == "y" and self.me_dict[me]["dim"] == 2:
            return self.me_dict[me]["y_bins"]
        else:
            raise ValueError("Invalid dimension or element is not 2D")

    def getDims(self, me):
        return self.me_dict[me]["dim"]

    def getExcluded(self):
        return self.excludelumis

    def getMENames(self):
        return list(self.me_dict.keys())

    def getEmptyLSs(self, me):
        return self.me_dict[me]["emptyLSs"]

    def getIntegral(self, me):
        return self.me_dict[me]["integral"]

    def getNorm(self, me):
        return self.me_dict[me]["norm"]

    def getTrigNorm(self, me):
        return self.me_dict[me]["trignorm"]

    def _setEmptyLSs(self, thrshld=0):
        for me in self.getMENames():
            isemptyLSs_arr = np.array(self.getEntries(me)) <= thrshld
            emptyLSs_idxs = np.where(isemptyLSs_arr)[0]
            self.me_dict[me]["emptyLSs"] = list(emptyLSs_idxs + 1)

    def setExcluded(self, excludelumis):
        if len(excludelumis) == 0:
            self.excludelumis = []
            return None
        ls_to_exclude = []
        for to_exclude in excludelumis:
            if isinstance(to_exclude, int):
                ls_to_exclude.append(to_exclude)
            elif isinstance(to_exclude, tuple):
                if (len(to_exclude) != 2) or (to_exclude[0] > to_exclude[1]):
                    raise Exception(
                        "Could not expand tuple into range of LSs to exclude. Make sure it has two elements and the first one is larger than the second."
                    )
                ls_to_exclude.extend(range(to_exclude[0], to_exclude[1] + 1))
            else:
                raise TypeError("Incompatible element type in list of LSs to exclude.")
        ls_to_exclude = sorted(set(ls_to_exclude))
        self.excludelumis = ls_to_exclude

    def normData(self, trigger_rate=None, mes=None):
        """
        For normalizing area under curve or by trigger rate.
        """
        if mes is None:
            mes = self.getMENames()
        if trigger_rate is None:
            self._areaNormalize(mes)
        else:
            self._trigNormalize(trigger_rate, mes)

    def _areaNormalize(self, mes=None):
        for me in mes:
            summation = self.getData(me).sum(axis=1, keepdims=True)
            self.me_dict[me]["norm"] = np.nan_to_num(
                self.me_dict[me]["data"] / summation, nan=0
            )

    def _trigNormalize(self, trigger_rate, mes=None):
        for me in self.getMENames():
            medata = self.getData(me)
            dims = self.getDims(me)
            if dims == 1:
                self.me_dict[me]["trignorm"] = medata / trigger_rate[:, np.newaxis]
            elif dims == 2:
                n = medata.shape[1]
                m = medata.shape[2]
                self.me_dict[me]["trignorm"] = medata / np.repeat(
                    trigger_rate[:, np.newaxis], n * m, axis=1
                ).reshape(-1, n, m)
            else:
                raise ValueError("Dimensions can only be 1 or 2.")

    def integrateData(self, norm=False, mes=None, exclude=[]):
        if len(exclude) > 0:
            self.setExcluded(exclude)
        for me in self.getMENames():
            if len(self.getExcluded()) > 0:
                excluded_indices = [int(x - 1) for x in self.getExcluded() if (x > 0)]
                data_to_integrate = np.delete(
                    self.getData(me), excluded_indices, axis=0
                )
            else:
                data_to_integrate = self.getData(me)
            integral = data_to_integrate.sum(axis=0, keepdims=True)[0]
            if norm:
                self.me_dict[me]["integral"] = integral / integral.sum()
            else:
                self.me_dict[me]["integral"] = integral
