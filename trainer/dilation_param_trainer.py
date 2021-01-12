import os
import torch
import torch.nn as nn
import numpy as np

import wandb
import matplotlib.pyplot as plt

from utils.model_utils import count_parameters
from models.dilation_param import GalerkinDE_dilationtest
# from utils.LBFGS import LBFGS, get_grad

class Trainer():
    def __init__(self, args, train_dataloader):
        self.train_dataloader = train_dataloader
        self.n_epochs = args.n_epochs

        self.model = GalerkinDE_dilationtest(args).cuda()
        # self.optimizer = LBFGS(self.model.parameters(), lr=args.lr, history_size=10, line_search='Armijo')
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=args.lr)

        self.path = args.path + args.filename + '.pt'
        print('start training!')
        print('number of params: {}'.format(count_parameters(self.model)))

        print('dataset_type: {}'.format(str(args.dataset_type)))
        print('description: {}'.format(str(args.description)))

        wandb.init(project='generativeode')
        wandb.config.update(args)
        wandb.watch(self.model, log='all')

    def train(self):
        print('filename: {}'.format(self.path))

        best_mse = float('inf')
        if os.path.exists(self.path):
            ckpt = torch.load(self.path)
            self.model.load_state_dict(ckpt['model_state_dict'])
            best_mse = ckpt['loss']
            print('loaded saved parameters')

        for n_epoch in range(self.n_epochs):
            for iter, sample in enumerate(self.train_dataloader):
                self.model.train()
                self.optimizer.zero_grad(set_to_none=True)

                samp_sin, samp_ts, latent_v = sample
                samp_sin = samp_sin.cuda() ; samp_ts = samp_ts.cuda() ; latent_v = latent_v.cuda()

                # opfun = lambda X: self.model.forward(samp_ts, samp_sin, latent_v)

                # grad, obj = get_grad(self.optimizer, np.ndarray(latent_v), np.ndarray(samp_sin), opfun)
                # p = self.optimizer.two_loop_recursion(-grad)

                train_loss = self.model(samp_ts, samp_sin, latent_v)
                train_loss.backward()
                self.optimizer.step()

                # obj, lr, _, _, _, _ = self.optimizer.step(p, grad)
                # obj.backward()
                # grad = self.optimizer._gather_flat_grad()

                # curvature update
                # self.optimizer.curvature_update(grad, eps=0.2, damping=True)

                if best_mse > train_loss:
                    best_mse = train_loss
                    torch.save({'model_state_dict': self.model.state_dict(), 'loss': best_mse}, self.path)
                    print('model parameter saved at epoch {}'.format(n_epoch))

                wandb.log({'train_loss': train_loss,
                           'best_mse': best_mse})

                self.result_plot(samp_sin[0], latent_v[0])
                self.check_dilation()


            print('epoch: {},  mse_loss: {}'.format(n_epoch, train_loss))


    def result_plot(self, samp_sin, latent_v):
        samp_sin = samp_sin.unsqueeze(0);
        latent_v = latent_v.unsqueeze(0)
        test_ts = torch.Tensor(np.linspace(0., 8 * np.pi, 2700)).unsqueeze(0).to(samp_sin.device)

        output = self.model.predict(test_ts, samp_sin, latent_v)
        amp = latent_v[0][0]
        test_tss = test_ts.squeeze()
        real_output = amp * (-4 * torch.sin(test_tss) + torch.sin(2 * test_tss) - torch.cos(test_tss) + 0.5 * torch.cos(2 * test_tss))

        # plot output
        fig = plt.figure(figsize=(16, 8))
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(test_ts.squeeze().cpu().numpy(), real_output.detach().cpu().numpy(), 'g', label='true trajectory')
        ax.plot(test_ts.squeeze().cpu().numpy(), output.squeeze().detach().cpu().numpy(), 'r',
                label='learned trajectory')

        wandb.log({"predict": wandb.Image(plt)})

        plt.close('all')

    def check_dilation(self):
        dilation = self.model.func.gallinear.dilation
        data = [str(i) for i in dilation.tolist()]
        wandb.log({'dilation': wandb.Table(data=data, columns=['1', '2', '3', '4', '5', '6'])})



