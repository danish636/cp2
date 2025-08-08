# import json
# with open('media/checklist/sector11.json', 'r') as f:
#     sector = json.loads(f.read().replace("Fi0cial","Financial"))
#
#
# f_re_fc_best = {}
# f_re_fc_base = {}
# f_re_fc_worst = {}
#
# f_re_er_best = {}
# f_re_er_base = {}
# f_re_er_worst = {}
# for i in sector:
#     if "ranking" not in i:
#         f_re_fc_best[i] = (sector[i]["Relative_best"] + sector[i]["FCFF_best"])/2
#         f_re_fc_base[i] = (sector[i]["Relative_base"] + sector[i]["FCFF_base"])/2
#         f_re_fc_worst[i] = (sector[i]["Relative_worst"] + sector[i]["FCFF_worst"])/2
#
#         f_re_er_best[i] = (sector[i]["Relative_best"] + sector[i]["ERM_best"])/2
#         f_re_er_base[i] = (sector[i]["Relative_base"] + sector[i]["ERM_base"])/2
#         f_re_er_worst[i] = (sector[i]["Relative_worst"] + sector[i]["ERM_worst"])/2
# sec = {}
# sec["ranking_relative_fcff_best"] = [k for k, v in sorted(f_re_fc_best.items(), key=lambda item: item[1])]
# sec["ranking_relative_fcff_base"] = [k for k, v in sorted(f_re_fc_base.items(), key=lambda item: item[1])]
# sec["ranking_relative_fcff_worst"] = [k for k, v in sorted(f_re_fc_worst.items(), key=lambda item: item[1])]
# sec["ranking_relative_erm_best"] = [k for k, v in sorted(f_re_er_best.items(), key=lambda item: item[1])]
# sec["ranking_relative_erm_base"] = [k for k, v in sorted(f_re_er_base.items(), key=lambda item: item[1])]
# sec["ranking_relative_erm_worst"] = [k for k, v in sorted(f_re_er_worst.items(), key=lambda item: item[1])]
# with open("sec.json", "w") as f:
#     f.write(json.dumps(sec))
#
# with open('media/checklist/industries11.json', 'r') as f:
#     sector = json.loads(f.read())
# f_re_fc_best = {}
# f_re_fc_base = {}
# f_re_fc_worst = {}
#
# f_re_er_best = {}
# f_re_er_base = {}
# f_re_er_worst = {}
# for i in sector:
#     if "ranking" not in i:
#         f_re_fc_best[i] = (sector[i]["Relative_best"] + sector[i]["FCFF_best"])/2
#         f_re_fc_base[i] = (sector[i]["Relative_base"] + sector[i]["FCFF_base"])/2
#         f_re_fc_worst[i] = (sector[i]["Relative_worst"] + sector[i]["FCFF_worst"])/2
#
#         f_re_er_best[i] = (sector[i]["Relative_best"] + sector[i]["ERM_best"])/2
#         f_re_er_base[i] = (sector[i]["Relative_base"] + sector[i]["ERM_base"])/2
#         f_re_er_worst[i] = (sector[i]["Relative_worst"] + sector[i]["ERM_worst"])/2
# ind = {}
#
# ind["ranking_relative_fcff_best"] = [k for k, v in sorted(f_re_fc_best.items(), key=lambda item: item[1])]
# ind["ranking_relative_fcff_base"] = [k for k, v in sorted(f_re_fc_base.items(), key=lambda item: item[1])]
# ind["ranking_relative_fcff_worst"] = [k for k, v in sorted(f_re_fc_worst.items(), key=lambda item: item[1])]
# ind["ranking_relative_erm_best"] = [k for k, v in sorted(f_re_er_best.items(), key=lambda item: item[1])]
# ind["ranking_relative_erm_base"] = [k for k, v in sorted(f_re_er_base.items(), key=lambda item: item[1])]
# ind["ranking_relative_erm_worst"] = [k for k, v in sorted(f_re_er_worst.items(), key=lambda item: item[1])]
#
# with open("ind.json", "w") as f:
#     f.write(json.dumps(ind))